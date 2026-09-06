from __future__ import annotations

import json
from unittest import mock

from green_v2.messaging.rabbitmq import DeliveryHandle, RabbitMqConsumer

from test_rabbitmq_adapter import isolated_settings


def test_consumer_uses_manual_ack_prefetch_and_generation_guard() -> None:
    connection = mock.Mock(is_open=True)
    channel = mock.Mock(is_open=True)
    connection.channel.return_value = channel
    method = mock.Mock(delivery_tag=17)
    channel.basic_get.return_value = (method, None, json.dumps({"message_id": "m-1"}).encode())
    with mock.patch(
        "green_v2.messaging.rabbitmq.pika.BlockingConnection",
        return_value=connection,
    ):
        consumer = RabbitMqConsumer(isolated_settings())
        delivery, payload = consumer.get_one("green_v2.raw.telemetry")

    assert delivery == DeliveryHandle(17, 1)
    assert payload == {"message_id": "m-1"}
    channel.basic_get.assert_called_once_with(queue="green_v2.raw.telemetry", auto_ack=False)
    channel.basic_qos.assert_called_once_with(prefetch_count=50)
    assert consumer.ack(delivery) is True
    assert consumer.ack(DeliveryHandle(18, 0)) is False
    channel.basic_ack.assert_called_once_with(delivery_tag=17)


def test_consumer_nack_requests_requeue() -> None:
    connection = mock.Mock(is_open=True)
    channel = mock.Mock(is_open=True)
    connection.channel.return_value = channel
    with mock.patch(
        "green_v2.messaging.rabbitmq.pika.BlockingConnection",
        return_value=connection,
    ):
        consumer = RabbitMqConsumer(isolated_settings())
        consumer.connect()
        assert consumer.nack(DeliveryHandle(9, 1), requeue=True) is True
    channel.basic_nack.assert_called_once_with(delivery_tag=9, requeue=True)
