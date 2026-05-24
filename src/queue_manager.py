import json
import os
import uuid

import boto3
from botocore.exceptions import ClientError

from src.logger import setup_logger

logger = setup_logger(__name__)

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


class SQSManager:
    """Manages sending and receiving messages from an AWS SQS queue."""

    def __init__(self, queue_url: str = SQS_QUEUE_URL, region: str = AWS_REGION):
        self.queue_url = queue_url
        self.client = boto3.client("sqs", region_name=region)

        if not self.queue_url:
            logger.warning("SQS_QUEUE_URL is not set. Queue operations will fail.")

    def send_message(
        self,
        url: str,
        use_browser: bool = False,
        proxy: str | None = None,
        job_id: str | None = None,
        metadata: dict | None = None,
    ) -> str | None:
        """Send a scraping task message to the SQS queue.

        Returns the SQS MessageId on success, or None on failure.
        """
        message_body = {
            "task_id": str(uuid.uuid4()),
            "url": url,
            "use_browser": use_browser,
            "proxy": proxy,
            "job_id": job_id,
            "metadata": metadata or {},
        }

        try:
            response = self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageGroupId=job_id or "default",
            )
            msg_id = response.get("MessageId")
            logger.info("SQS message sent: %s (url=%s)", msg_id, url)
            return msg_id
        except ClientError as exc:
            logger.error("Failed to send SQS message for %s: %s", url, exc)
            return None

    def send_batch(
        self,
        urls: list[str],
        use_browser: bool = False,
        proxy: str | None = None,
        job_id: str | None = None,
    ) -> int:
        """Send multiple URLs as individual messages. Returns count of successful sends."""
        success_count = 0
        # SQS SendMessageBatch supports max 10 per call
        batch_size = 10
        for i in range(0, len(urls), batch_size):
            chunk = urls[i:i + batch_size]
            entries = []
            for idx, url in enumerate(chunk):
                entries.append({
                    "Id": str(idx),
                    "MessageBody": json.dumps({
                        "task_id": str(uuid.uuid4()),
                        "url": url,
                        "use_browser": use_browser,
                        "proxy": proxy,
                        "job_id": job_id,
                        "metadata": {},
                    }),
                    "MessageGroupId": job_id or "default",
                })
            try:
                response = self.client.send_message_batch(
                    QueueUrl=self.queue_url,
                    Entries=entries,
                )
                success_count += len(response.get("Successful", []))
                failed = response.get("Failed", [])
                if failed:
                    logger.warning("SQS batch: %d messages failed.", len(failed))
            except ClientError as exc:
                logger.error("SQS batch send failed: %s", exc)

        logger.info("SQS batch complete: %d/%d messages sent.", success_count, len(urls))
        return success_count

    def poll_messages(
        self,
        max_messages: int = 10,
        wait_time: int = 20,
        visibility_timeout: int = 120,
    ) -> list[dict]:
        """Long-poll the SQS queue and return parsed message bodies.

        Each returned dict includes the parsed body and the ReceiptHandle
        for deletion after processing.
        """
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=wait_time,
                VisibilityTimeout=visibility_timeout,
            )
        except ClientError as exc:
            logger.error("SQS poll failed: %s", exc)
            return []

        messages = response.get("Messages", [])
        if not messages:
            logger.info("SQS poll: no messages available.")
            return []

        results = []
        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                body["_receipt_handle"] = msg["ReceiptHandle"]
                body["_message_id"] = msg["MessageId"]
                results.append(body)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Skipping malformed SQS message: %s", exc)

        logger.info("SQS poll: received %d messages.", len(results))
        return results

    def delete_message(self, receipt_handle: str) -> bool:
        """Delete a processed message from the queue."""
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
            return True
        except ClientError as exc:
            logger.error("Failed to delete SQS message: %s", exc)
            return False
