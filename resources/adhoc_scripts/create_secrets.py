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

import json
import boto3
import csv

from botocore.exceptions import ClientError

"""
    pre-requisites:
    1. A credentials.csv file in the current location in the below format.
    Header: servername,dbname,username,password,ipaddress,port,engine
    2. aws cli installed with the credentials

    Description : Script reads the credentials.csv file and create a secret under secretmanager for each row.
"""

def main():
    #Create boto3 client for AWS service secretmanager
    client = boto3.client('secretsmanager')

    #Open the file in read only and loop over each record for creating a secret for each dbname in the server.
    with open('./credentials.csv',mode='r') as csvfile :
      reader = csv.DictReader(csvfile)

      for row in reader:
        #Build the secretname using the servername and dbname
        SecretName = 'dms_{}_{}_sql_server'.format(row['servername'],row['dbname'])

        #create SecretString json with the credentials , ip and port details.
        SecretString = {
        "username":row['username'],
        "password":row['password'],
        "engine":row['engine'],
        "host":row['ipaddress'],
        "port":row['port'],
        "dbname":row['dbname']
        }

        #Invoice boto3 api create_secret for creating the secret in the account.
        try:
            response = client.create_secret(
                    Name = SecretName,
                    Description='Secrets stored for db server:{} and dbname :{}'.format(row['servername'],row['dbname']),
                    SecretString = json.dumps(SecretString)
                    )
            print(response)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                print("The requested secret " + SecretName + " already exists")

if __name__ == '__main__':
    main()
