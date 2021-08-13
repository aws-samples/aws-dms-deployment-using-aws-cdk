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

from aws_cdk import (
    core,
    aws_dms as dms
)
import os
import json
import boto3
import csv

class DmsCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, dms_target_s3_access_role, stage_bucket,
                  sns_topic,vpc_default_security_group, vpc_subnet_group, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)
        stack = core.Stack.of(self)


        params = {}

        # Determine account type based on env variable  for fetching common parameters
        # suitable instance class, max filesize that DMS split data into files and replicate to S3 stage bucket
        current_dir = os.path.dirname(__file__)
        param_path = '../resources/config/parameters.txt'

        # Open a reader to the csv, the delimiter is a single space
        with open(os.path.join(current_dir, param_path), mode='r') as infile:
            reader = csv.reader(infile, delimiter=',', skipinitialspace=True)
            next(reader)
            params = {key: row for key, *row in reader}

        dms_instance_class = params['instancesize'][0]
        target_max_file_size = params['maxfilesize'][0]
        task_migration_type = params['task_migration_type'][0]

        # boto3 client for Secrets Manager
        sm_client = boto3.client("secretsmanager")

        param_path = '../resources/config/dms_config_details.txt'
        with open(os.path.join(current_dir, param_path), mode='r') as csvfile:
            # Open a reader to the csv, the delimiter is a single space
            reader = csv.DictReader(csvfile)
            prevInstName = ''

            vpc_subnet_group_ids = []
            replication_subnet_group_identifier = 'aws-cdk-cdk-subnetgroup'
            for i in vpc_subnet_group:
                vpc_subnet_group_ids.append(i.subnet_id)

            subnet = dms.CfnReplicationSubnetGroup(
                self,
                "DMSReplicationSubnetGrp",
                replication_subnet_group_identifier=replication_subnet_group_identifier,
                replication_subnet_group_description='DMS replication subnet group',
                subnet_ids=vpc_subnet_group_ids
            )
            
            for row in reader:

                replInstName = "{}-instance".format(row["server"])
                replInstIdentifier= "{}-instance".format(row["server"])
                replTaskName = "{}-{}-all".format(row["server"],row["dbname"])
                sourceEndPoint = "{}-{}-sqlserver-source-endpoint".format(row["server"],row["dbname"])
                targetEndPoint = "{}-{}-s3-target-endpoint".format(row["server"],row["dbname"])
                SecretId = "dms_{}_{}_sql_server".format(row["server"],row["dbname"])
                s3_prefix = "data/{}/{}/".format(row["server"],row["dbname"])

                vpc_security_group_id = vpc_default_security_group


                #Fetch credentials for each database from AWS Secret manager
                get_secret_value_response = sm_client.get_secret_value(SecretId=SecretId)
                secret = get_secret_value_response['SecretString']
                secret = json.loads(secret)
                
                #Create replication instance per server
                if replInstName != prevInstName :
                    instance = dms.CfnReplicationInstance(
                        self,
                        replInstName,
                        replication_instance_identifier=replInstIdentifier,
                        replication_instance_class=dms_instance_class,
                        publicly_accessible=False,
                        replication_subnet_group_identifier=subnet.ref,
                        vpc_security_group_ids=[vpc_security_group_id],
                        auto_minor_version_upgrade=True,
                        multi_az=True,
                        engine_version='3.4.3'
                        )
                    
                prevInstName = replInstName

                # create source endpoint
                source = dms.CfnEndpoint(
                        self,
                        sourceEndPoint,
                        endpoint_identifier=sourceEndPoint,
                        endpoint_type='source',
                        engine_name=secret.get('engine'),
                        server_name=secret.get('host'),
                        port=int(secret.get('port')),
                        database_name=secret.get('dbname'),
                        username=secret.get('username'),
                        password=secret.get('password'),
                        ssl_mode="require"
                    )
    
                # create target endpoint
                target = dms.CfnEndpoint(
                        self,
                        targetEndPoint,
                        endpoint_identifier=targetEndPoint,
                        endpoint_type='target',
                        engine_name='s3',
                        s3_settings=dms.CfnEndpoint.S3SettingsProperty(
                            bucket_name=stage_bucket.bucket_name,
                            bucket_folder=s3_prefix,
                            compression_type="GZIP",
                            service_access_role_arn=dms_target_s3_access_role.role_arn
                        ),
                        extra_connection_attributes=f"encryptionMode=SSE_S3;timestampColumnName=TX_TIMESTAMP;dataFormat=parquet;parquetVersion=PARQUET_2_0;parquetTimestampInMillisecond=true;maxFileSize={target_max_file_size};",
                    )

                mappings_location = '../resources/config/dms_json_mappings/dms_{}_{}_mappings.json'.format(row["server"],row["dbname"])

                    
                with open(os.path.join(current_dir, mappings_location.lower()), mode='r') as jsonfile:
                    mappings_json = json.load(jsonfile)

                # create dms replication task
                task = dms.CfnReplicationTask(
                    self,
                    replTaskName,
                    replication_task_identifier=replTaskName,
                    replication_instance_arn=instance.ref,
                    migration_type=task_migration_type,
                    source_endpoint_arn=source.ref,
                    target_endpoint_arn=target.ref,
                    table_mappings=json.dumps(mappings_json)
                    )        

        # event notifcation if instance fails or task fails
        failure_event_instance = dms.CfnEventSubscription(
            self,
            "failure_event_instance",
            sns_topic_arn=sns_topic.topic_arn,
            enabled=True,
            event_categories=["failure"],
            source_type="replication-instance"
        )

        failure_event_task = dms.CfnEventSubscription(
            self,
            "failure_event_task",
            sns_topic_arn=sns_topic.topic_arn,
            enabled=True,
            event_categories=["failure"],
            source_type="replication-task"
        )

