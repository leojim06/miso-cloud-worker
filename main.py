from db import session
from task import Status, Task
from aws_client import sqs_client, s3_client
from config import SQS_URL, CARPETA_CARGA, CARPETA_DESCARGA, BUCKET_NAME
import schedule
import time
import json
import os
import ffmpeg
import boto3

# def autoscaling():
#     print('Iniciando consulta autoscaling')
#     sqs_client = boto3.client('sqs', region_name="us-east-1")
#     asg_client = boto3.client('autoscaling', region_name="us-east-1")
#     cw_client = boto3.client('cloudwatch', region_name="us-east-1")

#     sqs_queue_url = SQS_URL

#     # Fetch the ApproximateNumberOfMessages from the queue
#     sqs_queue_attributes = sqs_client.get_queue_attributes(QueueUrl=sqs_queue_url, AttributeNames=['ApproximateNumberOfMessages'])
#     number_of_messages = int(sqs_queue_attributes['Attributes']['ApproximateNumberOfMessages'])

#     # Fetch the details of the autoscaling 
#     asg_detail = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=['miso-worker-no-http'])

#     # Find the number of `InService` instances in the autoscaling group
#     asg_instances = asg_detail['AutoScalingGroups'][0]['Instances']
#     in_service_instances = len([i for i in asg_instances if i['LifecycleState'] == 'InService'])

#     # Calculate the BacklogPerInstance metric
#     if in_service_instances != 0:
#         backlog_per_instance = number_of_messages / in_service_instances
#     else:
#         backlog_per_instance = number_of_messages

#     # Push the metric to Cloudwatchput_metric_data
#     cw_client.put_metric_data(
#         Namespace='MyNamespace',
#         MetricData=[
#             {
#                 'MetricName': 'MyBacklogPerInstance',
#                 'Dimensions': [{'Name': 'MyOptionalMetricDimensionName','Value': 'MyOptionalMetricDimensionValue'}],
#                 'Value': backlog_per_instance,
#                 'Unit': 'None'
#             }
#         ]
#     )

#     print('Fin proceso consulta autoscaling')

def job():
    print("Iniciando Tarea")
    start = time.time()
    
    try:
        # convertidor
        # recuperar mensajes de la cola
        print('* SQS * - consultando cola')
        sqs = sqs_client()
        response = sqs.receive_message(
            QueueUrl=SQS_URL,
            MaxNumberOfMessages=1
        )

        if 'Messages' not in response:
            print('* SQS * - No hay mensajes en la cola')
            return False

        # Recuperar task de cola y de base de datos
        queue_message = response['Messages'][0]
        body = json.loads(queue_message['Body'])
        taskId = body["taskId"]
        print('* SQS * - obteniendo tarea {}'.format(taskId))
        t = session.query(Task).get(taskId)
        print('task obtenida: {} - {}'.format(t.status, t.fileName))

        if t:
            if t.status == Status.UPLOADED:
                t.status = Status.PROCESSED

                # S3
                try:
                    print('* S3 * - iniciando proceso')
                    fileName = t.fileName.split(".", 1)[0]
                    s3 = s3_client()
                    with open(CARPETA_CARGA.joinpath(t.fileName), 'wb') as file:
                        print('* S3 * - descargando archivo local')
                        s3.download_fileobj(BUCKET_NAME, f'files/upload/{t.fileName}', file)

                    print('* S3 * - realizando conversión')
                    source_file = CARPETA_CARGA.joinpath(t.fileName).resolve()
                    target_file = CARPETA_DESCARGA.joinpath(f"{fileName}.{t.newFormat.name}").resolve()
                    ffmpeg.input(str(source_file)).output(str(target_file)).overwrite_output().run()

                    with open(CARPETA_DESCARGA.joinpath(f"{fileName}.{t.newFormat.name}"), 'rb') as file:
                        print('* S3 * - subiendo archivo a bucket')
                        s3.upload_fileobj(file, BUCKET_NAME, 'files/download/' + '{}.{}'.format(fileName, t.newFormat.name))

                    # borrar archivos locales
                    print('* S3 * - borrando archivos locales')
                    os.remove(str(source_file))
                    os.remove(str(target_file))

                    session.commit()

                    # SQS
                    print('* SQS * - eliminar de la cola')
                    receipt_handle = queue_message['ReceiptHandle']
                    delete_response = sqs.delete_message(
                        QueueUrl=SQS_URL,
                        ReceiptHandle=receipt_handle
                    )
                    print('* SQS * - Mensaje borrado')

                    end = time.time()
                    print("Tarea realizada en: " + str(end - start))
                    return True

                except Exception as e:
                    print(e.args)
                    session.rollback()
                    return False
            else:
                # SQS
                print('* SQS * - eliminar de la cola')
                receipt_handle = queue_message['ReceiptHandle']
                delete_response = sqs.delete_message(
                    QueueUrl=SQS_URL,
                    ReceiptHandle=receipt_handle
                )
                print('* SQS * - Mensaje borrado')
                return False
        else:
            return False

    except Exception as ex:
        print("Error procesando tarea", ex)

def main():
    schedule.every(2).seconds.do(job)
    # schedule.every(15).seconds.do(autoscaling)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
