# /*
#  * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  * SPDX-License-Identifier: MIT-0
#  *
#  * Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  * software and associated documentation files (the "Software"), to deal in the Software
#  * without restriction, including without limitation the rights to use, copy, modify,
#  * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  * permit persons to whom the Software is furnished to do so.
#  *
#  * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#  * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#  * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#  */

import boto3
import csv
import time

"""
pre-requisites:
  1. A credentials.csv file in the current location in the below format.
  Header: servername,dbname,username,password,ipaddress,port,engine
  2. aws cli installed with the credentials or run it in the aws cloud shell 

  Description : Script triggers the function starts the dms replication task created for each database listed in credentials.csv file.
  
"""

def main():
    #Create boto3 client for AWS DMS service
    client = boto3.client('dms')

    #Open the file in read only and loop over each record for modifying and starting the dms task
    with open('./credentials.csv',mode='r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            #Building the task name using servername and dbname from the file
            task_name = '{}-{}-all'.format(row['servername'],row['dbname'])
            print('Working on task:{}'.format(task_name))

            #Fetching the task parameters using the api call describe_replication tasks
            response = client.describe_replication_tasks(
                    Filters = [
                        {
                            'Name' : 'replication-task-id',
                            'Values' : [ task_name ]
                        }
                    ],
                    WithoutSettings=True
                )
            taskArn = response['ReplicationTasks'][0]['ReplicationTaskArn']

            #Modify replication task to enable cloudwatch logs since CDK do not support
            print('Modifying the replication task : {} for enabling cloudwatch logs'.format(task_name))
            response = client.modify_replication_task(
                    ReplicationTaskArn= taskArn,
                    ReplicationTaskIdentifier=task_name,
                    ReplicationTaskSettings="{\"Logging\": {\"EnableLogging\": true}}"
                )
            print('{}-Task Status:{}'.format(task_name,response['ReplicationTask']['Status']))

            #Poll DMS task every 15 secs to identify if the task state set back to Ready
            print('Waiting for the task to be Ready State')
            waiter_min = 20 #5 mins - Sleep 15 secs each time
            for attempt in range(waiter_min) :
                response = client.describe_replication_tasks(
                        Filters = [
                            {
                                'Name' : 'replication-task-id',
                                'Values' : [ task_name ]
                            }
                        ],
                        WithoutSettings=True
                    )

                if response['ReplicationTasks'][0]['Status'] == "ready" :
                    print('Task status is Ready and resuming/start the task')
                    break
                else :
                    time.sleep(15)
                    print(attempt)

            #Calling boto3 api start_replicaiton_task for starting the DMS task
            print('Starting replication_task:{}'.format(task_name))
            response = client.start_replication_task(
                    ReplicationTaskArn=taskArn,
                    StartReplicationTaskType= 'start-replication'
                )
            print('{} task status : {}'.format(task_name,response['ReplicationTask']['Status']))


if __name__ == '__main__':
    main()
