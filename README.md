# S.C.A.L.E. (Scheduler for Carbon-Aware Load Execution)

This is the accompanying code for the similarly named thesis available at [http://resolver.tudelft.nl/uuid:79406c06-ab43-4cba-9136-cb8243e891ed](http://resolver.tudelft.nl/uuid:79406c06-ab43-4cba-9136-cb8243e891ed).

## Summary
The global climate change crisis and the associated phenomenon of global warming have taken center stage in recent years.
Greenhouse gas emissions due to electricity generation are a contributor to this problem.
Internet Services running in data centers consume enormous amounts of energy and should be optimized to reduce their greenhouse gas emissions.

This thesis explores the possibility of intelligently scheduling resource-intensive batch data-processing jobs to green energy generation hours in the day.
Green hours are hours within the day during which the amount of greenhouse gasses emitted per kilowatt-hour (kWh) is lower compared to other hours of the day.
There is a variance in the amount of emissions due to the variability of renewable energy generation and grid demand.

The system "_S.C.A.L.E._ (Scheduler for Carbon-Aware Load Execution)" is proposed.
It schedules compute jobs to periods of low-carbon-intense energy generation based on predictions of renewable energy generation and grid demand.
The system was evaluated against a simulated data processing pipeline at a company; this pipeline is one of the larger consumers of that companies private cloud.
The scheduler aims to reduce greenhouse gas emissions by intelligently predicting task running times and green hours for the next day and optimizing the times at which tasks are processed throughout the day.

Several main conclusions are drawn based on this research:
1. The accuracy of task load predictions regarding running times is crucial for effective scheduling.
The research concludes that, with sufficient historical data, the scheduler can predict task running times with an acceptable margin of error (5-10%).
2. The research explores the scheduler's ability to predict periods of low carbon intensity and the resulting reduction in carbon emissions by implementing it.
The research affirms the scheduler's accuracy in determining low-carbon-intensive energy generation periods and estimates a potential 20\% reduction in greenhouse gas emissions.
3. The potential overhead introduced by implementing a carbon-aware scheduler is addressed.
The research identifies that while the scheduling algorithm itself is lightweight, the concurrent processing of tasks introduces overhead.
The tipping point, where the overhead outweighs the benefits, varies for each system and should be experimentally determined.

The thesis concludes by emphasizing the significance of implementing a carbon-aware scheduler to reduce the environmental impact of data centers.
The proposed scheduler is a promising contribution to sustainable computing practices.
Further, the research suggests the need for continued work and adoption of the scheduler into production environments, especially within the context of the companies data processing pipeline.

The repository is pre-configured to run the full system test, enabling the collection of similar data to the thesis.
Note that these tests require a rather large amount of resources and are expected to run for several hours to days,
depending on the processing power available.

## Installation
### Prerequisites
- Python 3.11
- docker
- docker-compose
- poetry
- A django compatible database (e.g., PostgreSQL)

### Installation
1. Clone the repository
2. Install dependencies using poetry: `poetry install`
3. Build the docker images: `docker compose build`
4. Start the docker containers: `docker compose up -d`

## Usage
Depending on the settings in [scheduler/settings.toml](scheduler/settings.toml), the environment will start the full
system, with the scheduler and all the components.

### Running the evaluations
The evaluations can be run by changing the values in [scheduler/settings.toml](scheduler/settings.toml) and starting
up the environment using `docker-compose up -d`.

The evaluations require the synthetic twitch dataset.
To gather this, run the shell script at [scheduler/synthetic/synth-data/unpack.sh](scheduler/synthetic/synth-data/unpack.sh)
Then, run all code in the [scheduler/synthetic/synth-data/create-daily-test-data.ipynb](scheduler/synthetic/synth-data/create-daily-test-data.ipynb)
jupyter notebook to create the daily test data.

The system should then be ready to run the evaluations.
