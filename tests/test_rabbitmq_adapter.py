from __future__ import annotations

import os
from unittest import mock

from green_v2.config import Settings
from green_v2.messaging.rabbitmq import RabbitMqDeliveryAcknowledger, RabbitMqPublisher


def isolated_settings() -> Settings:
    with mock.patch.dict(os.environ, {}, clear=True):
        return Settings.from_env()


def test_publisher_declares_durable_queues_and_persistent_messages() -> None:
    connection = mock.Mock(is_open=True)
    channel = mock.Mock(is_open=True)
    connection.channel.return_value = channel
    with mock.patch(
        "green_v2.messaging.rabbitmq.pika.BlockingConnection",
        return_value=connection,
    ):
        publisher = RabbitMqPublisher(isolated_settings())
        publisher.publish("green_v2.raw.telemetry", {"message_id": "m-1"})

    declared = {call.kwargs["queue"] for call in channel.queue_declare.call_args_list}
    assert declared == {
        "green_v2.raw.telemetry",
        "green_v2.parsed.telemetry",
        "green_v2.failed",
        "green_v2.dlq",
    }
    assert all(call.kwargs["durable"] is True for call in channel.queue_declare.call_args_list)
    publish = channel.basic_publish.call_args.kwargs
    assert publish["exchange"] == ""
    assert publish["routing_key"] == "green_v2.raw.telemetry"
    assert publish["properties"].delivery_mode == 2


def test_delivery_acknowledger_maps_ack_and_requeue_nack() -> None:
    channel = mock.Mock()
    acknowledger = RabbitMqDeliveryAcknowledger(channel)
    assert acknowledger.ack(7) is True
    assert acknowledger.nack(8, requeue=True) is True
    channel.basic_ack.assert_called_once_with(delivery_tag=7)
    channel.basic_nack.assert_called_once_with(delivery_tag=8, requeue=True)
