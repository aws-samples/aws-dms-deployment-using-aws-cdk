import json
import pytest

from aws_cdk import core
from dms_cdk.dms_cdk_stack import DmsCdkStack


def get_template():
    app = core.App()
    DmsCdkStack(app, "dms-cdk")
    return json.dumps(app.synth().get_stack("dms-cdk").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())


def test_sns_topic_created():
    assert("AWS::SNS::Topic" in get_template())
