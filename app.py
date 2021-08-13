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

#!/usr/bin/env python3

from aws_cdk import core
from dms_cdk.dms_cdk_stack import DmsCdkStack
from dms_cdk.s3 import S3Stack
from dms_cdk.iam import IamStack
from dms_cdk.sns import SnsStack
from dms_cdk.vpc import VpcStack


app = core.App()

#Below stacks gets deployed to AWS account in the form CFN and deploy the aws services
iam_stack = IamStack(app, "IamStack")
s3_stack = S3Stack(app, "S3Stack")
sns_stack = SnsStack(app, "SnsStack")
vpc_stack = VpcStack(app,"VpcStack")
dms_stack = DmsCdkStack(app, "DmsStack",
    iam_stack.dms_target_s3_access_role,
    s3_stack.stage_bucket,
    sns_stack.sns_topic,
    vpc_stack.vpc.vpc_default_security_group,
    vpc_stack.vpc.private_subnets
)

app.synth()
