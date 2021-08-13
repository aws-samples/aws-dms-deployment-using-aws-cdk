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

from aws_cdk import core
import aws_cdk.aws_s3 as s3
import aws_cdk.core as Core
import os

current_dir = os.path.dirname(__file__)

class S3Stack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, repo_name: str=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stage_bucket = s3.Bucket(self, "datalake-stage",
            block_public_access= s3.BlockPublicAccess.BLOCK_ALL,
            encryption= s3.BucketEncryption.S3_MANAGED,
            metrics=[{"id": "EntireBucket"}]
        )

        # Bucket Lifecycle Policies
        self.stage_bucket.add_lifecycle_rule(
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Core.Duration.days(365 * 1)
                )
            ]
        )
