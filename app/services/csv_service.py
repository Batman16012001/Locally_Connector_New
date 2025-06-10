import pandas as pd
import logging
import gc
from typing import List, Dict, Any, Optional
from app.config.database import Database
from app.config.settings import get_settings
from app.models.product import Product
from app.services.job_service import JobService
from app.models.job import JobStatus
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import UploadFile
import io

settings = get_settings()
logger = logging.getLogger(__name__)


class CSVService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.products
        self.job_service = JobService(db)

    def parse_bool(self, val):
        """Parse a value to boolean, handling both string and boolean inputs."""
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.strip().lower() == "true"
        return False

    async def process_csv(self, file: UploadFile) -> Dict[str, Any]:
        """Process a CSV file and store its contents in MongoDB"""
        try:
            # Read the CSV file
            contents = await file.read()
            df = pd.read_csv(io.BytesIO(contents))

            # Convert DataFrame to list of dictionaries
            records = df.to_dict("records")

            # Insert records into MongoDB
            if records:
                result = await self.collection.insert_many(records)
                return {
                    "total_records": len(records),
                    "inserted_ids": len(result.inserted_ids),
                }
            else:
                return {"total_records": 0, "inserted_ids": 0}

        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise

    async def process_csv_with_job(
        self, file_path: str, job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a CSV file and insert records into MongoDB.
        If job_id is provided, update job progress.
        """
        try:
            # Update job status to processing if job_id is provided
            if job_id:
                await self.job_service.update_job_status(job_id, JobStatus.PROCESSING)

            # Read CSV in chunks to handle large files
            chunk_size = settings.batch_size
            total_records = 0
            successful_records = 0
            failed_records = 0
            errors = []
            batch_number = 0
            processed_records = 0

            # Count total records first if job_id is provided
            if job_id:
                for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                    total_records += len(chunk)
                await self.job_service.update_job_progress(
                    job_id, processed_records=0, total_records=total_records
                )
                # Reset file pointer
                total_records = 0

            # Process the CSV in chunks
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                records = chunk.to_dict("records")
                batch_number += 1
                total_records += len(records)
                print(f"Starting batch {batch_number} with {len(records)} records...")

                # Process each record
                valid_records = []
                chunk_successful = 0
                chunk_failed = 0
                chunk_errors = []

                for record in records:
                    try:
                        # Convert record to Product model
                        product = Product(
                            lcid=int(record["LCID"]),
                            lcid_slug=record["LCID_slug"],
                            variant_barcode=str(record["Variant Barcode"]),
                            variant_inventory_qty=int(record["Variant Inventory Qty"]),
                            handle=record["Handle"],
                            vendor=record["Vendor"],
                            product_gender=record["Product Gender"],
                            title=record["Title"],
                            tags=(
                                record["Tags"].split(",")
                                if pd.notna(record["Tags"])
                                else []
                            ),
                            type=record["Type"],
                            option1_name=(
                                record["Option1 Name"]
                                if pd.notna(record["Option1 Name"])
                                else None
                            ),
                            option1_value=(
                                record["Option1 Value"]
                                if pd.notna(record["Option1 Value"])
                                else None
                            ),
                            option2_name=(
                                record["Option2 Name"]
                                if pd.notna(record["Option2 Name"])
                                else None
                            ),
                            option2_value=(
                                record["Option2 Value"]
                                if pd.notna(record["Option2 Value"])
                                else None
                            ),
                            variant_price=float(record["Variant Price"]),
                            variant_compare_at_price=(
                                float(record["Variant Compare At Price"])
                                if pd.notna(record["Variant Compare At Price"])
                                else None
                            ),
                            variant_image=(
                                record["Variant Image"]
                                if pd.notna(record["Variant Image"])
                                else None
                            ),
                            body_html=(
                                record["Body HTML"]
                                if pd.notna(record["Body HTML"])
                                else None
                            ),
                            published=self.parse_bool(record["Published"]),
                            gift_card=self.parse_bool(record["Gift Card"]),
                            weight_lbs=(
                                float(record["Weight LBs"])
                                if pd.notna(record["Weight LBs"])
                                else None
                            ),
                        )
                        valid_records.append(product.model_dump())
                        chunk_successful += 1
                    except Exception as e:
                        chunk_failed += 1
                        error_msg = f"Error processing record {record.get('LCID', 'unknown')}: {str(e)}"
                        chunk_errors.append(error_msg)
                        if job_id:
                            await self.job_service.add_job_error(job_id, error_msg)

                # Insert valid records in batch
                if valid_records:
                    await self.collection.insert_many(valid_records)

                # Update counters
                successful_records += chunk_successful
                failed_records += chunk_failed
                errors.extend(chunk_errors)
                processed_records += len(records)

                # Update job progress if job_id is provided
                if job_id:
                    await self.job_service.update_job_progress(
                        job_id,
                        processed_records=processed_records,
                        total_records=total_records,
                        successful_records=successful_records,
                        failed_records=failed_records,
                    )

                # Force garbage collection after each chunk
                gc.collect()

            # Prepare result
            result = {
                "total_records": total_records,
                "successful_records": successful_records,
                "failed_records": failed_records,
                "errors": errors,
            }

            # Update job status and result if job_id is provided
            if job_id:
                await self.job_service.update_job_result(job_id, result)
                await self.job_service.update_job_status(job_id, JobStatus.COMPLETED)

            return result

        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")

            # Update job status to failed if job_id is provided
            if job_id:
                await self.job_service.add_job_error(job_id, f"Fatal error: {str(e)}")
                await self.job_service.update_job_status(job_id, JobStatus.FAILED)

            raise
