import subprocess

from dagster import (
    op,
    job,
    get_dagster_logger,
    ScheduleDefinition,
    RunFailureSensorContext,
    run_failure_sensor,
    Definitions,
)


def _run(command, cwd=None):
    logger = get_dagster_logger()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception(f"Command failed: {' '.join(command)}\n{result.stderr}")
    return result.stdout


@op
def scrape_telegram_data():
    _run(["python", "src/scraper.py"])
    return "scrape_done"


@op
def load_raw_to_postgres(scrape_done):
    _run(["python", "src/load_to_postgres.py"])
    return "load_done"


@op
def run_yolo_enrichment(load_done):
    _run(["python", "src/yolo_detect.py"])
    _run(["python", "src/load_yolo_to_postgres.py"])
    return "yolo_done"


@op
def run_dbt_transformations(yolo_done):
    _run(["dbt", "run"], cwd="medical_warehouse")
    _run(["dbt", "test"], cwd="medical_warehouse")
    return "dbt_done"


@job
def medical_warehouse_pipeline():
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(scraped)
    enriched = run_yolo_enrichment(loaded)
    run_dbt_transformations(enriched)


daily_schedule = ScheduleDefinition(
    job=medical_warehouse_pipeline,
    cron_schedule="0 6 * * *",
    execution_timezone="UTC",
)


@run_failure_sensor
def pipeline_failure_alert(context: RunFailureSensorContext):
    logger = get_dagster_logger()
    logger.error(
        f"Pipeline run {context.dagster_run.run_id} FAILED. "
        f"Failure event: {context.failure_event.message}"
    )


defs = Definitions(
    jobs=[medical_warehouse_pipeline],
    schedules=[daily_schedule],
    sensors=[pipeline_failure_alert],
)
