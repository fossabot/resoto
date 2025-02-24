from datetime import datetime
from typing import ClassVar, Dict, List, Optional, Type

from attrs import define, field

from resoto_plugin_aws.aws_client import AwsClient
from resoto_plugin_aws.resource.base import AwsApiSpec, AwsResource, GraphBuilder
from resoto_plugin_aws.resource.kms import AwsKmsKey
from resotolib.baseresources import ModelReference
from resotolib.graph import Graph
from resotolib.json_bender import F, Bender, S, AsInt, AsBool, Bend, ParseJson
from resotolib.types import Json
from resotolib.utils import utc_str

service_name = "sqs"


@define(eq=False, slots=False)
class AwsSqsRedrivePolicy:
    kind: ClassVar[str] = "aws_sqs_redrive_policy"
    kind_display: ClassVar[str] = "AWS SQS Redrive Policy"
    kind_description: ClassVar[str] = (
        "The AWS SQS Redrive Policy enables you to configure dead-letter queues for"
        " your Amazon Simple Queue Service (SQS) queues. Dead-letter queues are used"
        " to store messages that cannot be processed successfully by the main queue."
    )
    mapping: ClassVar[Dict[str, Bender]] = {
        "dead_letter_target_arn": S("deadLetterTargetArn"),
        "max_receive_count": S("maxReceiveCount"),
    }
    dead_letter_target_arn: Optional[str] = None
    max_receive_count: Optional[int] = None


@define(eq=False, slots=False)
class AwsSqsQueue(AwsResource):
    kind: ClassVar[str] = "aws_sqs_queue"
    kind_display: ClassVar[str] = "AWS SQS Queue"
    kind_description: ClassVar[str] = (
        "SQS (Simple Queue Service) is a fully managed message queuing service"
        " provided by Amazon Web Services. It enables you to decouple and scale"
        " microservices, distributed systems, and serverless applications."
    )
    api_spec: ClassVar[AwsApiSpec] = AwsApiSpec(service_name, "list-queues", "QueueUrls")
    reference_kinds: ClassVar[ModelReference] = {
        "successors": {"default": ["aws_kms_key"]},
        "predecessors": {"delete": ["aws_kms_key"]},
    }
    mapping: ClassVar[Dict[str, Bender]] = {
        "id": S("QueueName"),
        "name": S("QueueName"),
        "ctime": S("CreatedTimestamp") >> AsInt() >> F(lambda x: utc_str(datetime.utcfromtimestamp(x))),
        "mtime": S("LastModifiedTimestamp") >> AsInt() >> F(lambda x: utc_str(datetime.utcfromtimestamp(x))),
        "arn": S("QueueArn"),
        "sqs_queue_url": S("QueueUrl"),
        "sqs_approximate_number_of_messages": S("ApproximateNumberOfMessages") >> AsInt(),
        "sqs_approximate_number_of_messages_not_visible": S("ApproximateNumberOfMessagesNotVisible") >> AsInt(),
        "sqs_approximate_number_of_messages_delayed": S("ApproximateNumberOfMessagesDelayed") >> AsInt(),
        "sqs_policy": S("Policy") >> ParseJson(keys_to_snake=True),
        "sqs_redrive_policy": S("RedrivePolicy") >> ParseJson() >> Bend(AwsSqsRedrivePolicy.mapping),
        "sqs_fifo_queue": S("FifoQueue") >> AsBool(),
        "sqs_content_based_deduplication": S("ContentBasedDeduplication") >> AsBool(),
        "sqs_kms_master_key_id": S("KmsMasterKeyId"),
        "sqs_kms_data_key_reuse_period_seconds": S("KmsDataKeyReusePeriodSeconds") >> AsInt(),
        "sqs_deduplication_scope": S("DeduplicationScope"),
        "sqs_fifo_throughput_limit": S("FifoThroughputLimit"),
        "sqs_redrive_allow_policy": S("RedriveAllowPolicy") >> ParseJson() >> S("redrivePermission"),
        "sqs_visibility_timeout": S("VisibilityTimeout") >> AsInt(),
        "sqs_maximum_message_size": S("MaximumMessageSize") >> AsInt(),
        "sqs_message_retention_period": S("MessageRetentionPeriod") >> AsInt(),
        "sqs_delay_seconds": S("DelaySeconds") >> AsInt(),
        "sqs_receive_message_wait_time_seconds": S("ReceiveMessageWaitTimeSeconds") >> AsInt(),
        "sqs_managed_sse_enabled": S("SqsManagedSseEnabled") >> AsBool(),
    }
    sqs_queue_url: Optional[str] = field(default=None)
    sqs_approximate_number_of_messages: Optional[int] = field(default=None)
    sqs_approximate_number_of_messages_not_visible: Optional[int] = field(default=None)
    sqs_approximate_number_of_messages_delayed: Optional[int] = field(default=None)
    sqs_policy: Optional[Json] = field(default=None)
    sqs_redrive_policy: Optional[AwsSqsRedrivePolicy] = field(default=None)
    sqs_fifo_queue: Optional[bool] = field(default=None)
    sqs_content_based_deduplication: Optional[bool] = field(default=None)
    sqs_kms_master_key_id: Optional[str] = field(default=None)
    sqs_kms_data_key_reuse_period_seconds: Optional[int] = field(default=None)
    sqs_deduplication_scope: Optional[str] = field(default=None)
    sqs_fifo_throughput_limit: Optional[str] = field(default=None)
    sqs_redrive_allow_policy: Optional[str] = field(default=None)
    sqs_visibility_timeout: Optional[int] = field(default=None)
    sqs_maximum_message_size: Optional[int] = field(default=None)
    sqs_message_retention_period: Optional[int] = field(default=None)
    sqs_delay_seconds: Optional[int] = field(default=None)
    sqs_receive_message_wait_time_seconds: Optional[int] = field(default=None)
    sqs_managed_sse_enabled: Optional[bool] = field(default=None)

    @classmethod
    def called_collect_apis(cls) -> List[AwsApiSpec]:
        return [
            cls.api_spec,
            AwsApiSpec(service_name, "get-queue-attributes"),
            AwsApiSpec(service_name, "list-queue-tags"),
        ]

    @classmethod
    def collect(cls: Type[AwsResource], json: List[Json], builder: GraphBuilder) -> None:
        def add_instance(queue_url: str) -> None:
            queue_attributes = builder.client.get(
                service_name, "get-queue-attributes", "Attributes", QueueUrl=queue_url, AttributeNames=["All"]
            )
            if queue_attributes is not None:
                queue_attributes["QueueUrl"] = queue_url
                queue_attributes["QueueName"] = queue_url.rsplit("/", 1)[-1]
                if instance := cls.from_api(queue_attributes, builder):
                    builder.add_node(instance)
                    builder.submit_work(service_name, add_tags, instance)

        def add_tags(queue: AwsSqsQueue) -> None:
            tags = builder.client.get(service_name, "list-queue-tags", result_name="Tags", QueueUrl=queue.sqs_queue_url)
            if tags:
                queue.tags = tags

        for queue_url in json:
            if isinstance(queue_url, str):
                add_instance(queue_url)

    def connect_in_graph(self, builder: GraphBuilder, source: Json) -> None:
        if self.sqs_kms_master_key_id:
            builder.dependant_node(
                self,
                clazz=AwsKmsKey,
                id=self.sqs_kms_master_key_id,
            )

    def update_resource_tag(self, client: AwsClient, key: str, value: str) -> bool:
        client.call(
            aws_service=service_name,
            action="tag-queue",
            result_name=None,
            QueueUrl=self.sqs_queue_url,
            Tags={key: value},
        )
        return True

    def delete_resource_tag(self, client: AwsClient, key: str) -> bool:
        client.call(
            aws_service=service_name, action="untag-queue", result_name=None, QueueUrl=self.sqs_queue_url, TagKeys=[key]
        )
        return True

    def delete_resource(self, client: AwsClient, graph: Graph) -> bool:
        client.call(aws_service=service_name, action="delete-queue", result_name=None, QueueUrl=self.sqs_queue_url)
        return True

    @classmethod
    def called_mutator_apis(cls) -> List[AwsApiSpec]:
        return [
            AwsApiSpec(service_name, "tag-queue"),
            AwsApiSpec(service_name, "untag-queue"),
            AwsApiSpec(service_name, "delete-queue"),
        ]


resources: List[Type[AwsResource]] = [AwsSqsQueue]
