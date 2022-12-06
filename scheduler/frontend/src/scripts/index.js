import '../styles/index.scss';

import 'core-js/stable';
import $ from 'jquery';
import 'bootstrap/dist/js/bootstrap.bundle';
import { Chart } from 'chart.js/auto';
import 'chartjs-adapter-moment';
import moment from 'moment-timezone';
import { PSR_COLOR_MAP, PSR_COLOR_MAP_DARKER } from './psrTypeToColor';

const DAY_AHEAD_FORECAST_SOLAR_WIND_CHART_CONTAINER_ID = 'dayAheadForecastSolarWindChartContainer';
const DAY_AHEAD_FORECAST_TOTAL_LOAD_CHART_CONTAINER_ID = 'dayAheadForecastTotalLoadChartContainer';
const ACTUAL_GENERATION_CHART_CONTAINER_ID = 'actualGenerationChartContainer';
const RENEWABLE_PERCENTAGE_CHART_CONTAINER_ID = 'renewablePercentageChartContainer';

const DAY_AHEAD_FORECAST_SOLAR_WIND_CHART_CANVAS_ID = 'dayAheadForecastSolarWindChartCanvas';
const DAY_AHEAD_FORECAST_TOTAL_LOAD_CHART_CANVAS_ID = 'dayAheadForecastTotalLoadChartCanvas';
const ACTUAL_GENERATION_CHART_CANVAS_ID = 'actualGenerationChartCanvas';
const RENEWABLE_PERCENTAGE_CHART_CANVAS_ID = 'renewablePercentageChartCanvas';

let dayAheadForecastSolarWindChartContainer;
let dayAheadForecastTotalLoadChartContainer;
let actualGenerationChartContainer;
let renewablePercentageChartContainer;

let dayAheadForecastSolarWindChartCanvas;
let dayAheadForecastTotalLoadChartCanvas;
let actualGenerationChartCanvas;
let renewablePercentageChartCanvas;

let chartsStartDate;
let chartsEndDate;

let startDateFormatted;
let endDateFormatted;

const TIMEZONE = 'Europe/Amsterdam';
const CHART_TITLE_DATE_FORMAT = 'MMMM Do YYYY';
const formatXAxisTick = function (val) {
  return moment.tz(val, TIMEZONE)
    .format('MMM D, HH:mm');
};

function updateChartDatesFormatted() {
  startDateFormatted = moment.tz(chartsStartDate, TIMEZONE)
    .format(CHART_TITLE_DATE_FORMAT);
  endDateFormatted = moment.tz(chartsEndDate, TIMEZONE)
    .format(CHART_TITLE_DATE_FORMAT);
  return {
    startDateFormatted,
    endDateFormatted,
  };
}

const PSR_TYPES = Object.freeze({
  SOLAR: 'B16',
  WIND_OFFSHORE: 'B18',
  WIND_ONSHORE: 'B19',
});

function renderDayAheadForecastSolarWindChart() {
  console.count('renderDayAheadForecastSolarWindChart');
  const ctx = dayAheadForecastSolarWindChartCanvas.get(0)
    .getContext('2d');

  new Chart(ctx, {
    type: 'line',
    options: {
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        x: {
          type: 'time',
          ticks: {
            callback: formatXAxisTick,
          },
        },
        y: {
          ticks: {
            callback(val) {
              return `${val.toLocaleString()} mWh`;
            },
          },
        },
      },
      datasets: {
        line: {
          pointRadius: 0, // disable for all `'line'` datasets
        },
      },
      plugins: {
        title: {
          display: true,
        },
      },
    },
  });
}

function renderActualGenerationChart() {
  console.count('renderActualGenerationChart');
  const ctx = actualGenerationChartCanvas.get(0)
    .getContext('2d');

  new Chart(ctx, {
    type: 'line',
    options: {
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        x: {
          type: 'time',
          ticks: {
            callback: formatXAxisTick,
          },
        },
        y: {
          ticks: {
            callback(val) {
              return `${val.toLocaleString()} mWh`;
            },
          },
        },
      },
      datasets: {
        line: {
          pointRadius: 0, // disable for all `'line'` datasets
        },
      },
      plugins: {
        title: {
          display: true,
        },
      },
    },
  });
}

function renderDayAheadForecastTotalLoadChart() {
  console.count('renderDayAheadForecastTotalLoadChart');
  const ctx = dayAheadForecastTotalLoadChartCanvas.get(0)
    .getContext('2d');

  new Chart(ctx, {
    type: 'line',
    options: {
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        x: {
          type: 'time',
          ticks: {
            callback: formatXAxisTick,
          },
        },
        y: {
          ticks: {
            callback(val) {
              return `${val.toLocaleString()} mWh`;
            },
          },
        },
      },
      datasets: {
        line: {
          pointRadius: 0, // disable for all `'line'` datasets
        },
      },
      plugins: {
        title: {
          display: true,
        },
      },
    },
  });
}

function renderRenewablePercentageChart() {
  console.count('renderRenewablePercentageChart');

  const ctx = renewablePercentageChartCanvas.get(0)
    .getContext('2d');

  new Chart(ctx, {
    type: 'line',
    options: {
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        x: {
          type: 'time',
          ticks: {
            callback: formatXAxisTick,
          },
        },
        y: {
          ticks: {
            callback(val) {
              return `${val.toLocaleString()}%`;
            },
          },
        },
      },
      datasets: {
        line: {
          pointRadius: 0, // disable for all `'line'` datasets
        },
      },
      plugins: {
        title: {
          display: true,
        },
      },
    },
  });
}

function scaleChart(chart) {
  // Is passed in from template
  // eslint-disable-next-line no-undef
  if (SQUEEZED) {
    return;
  }
  const theChart = chart;
  theChart.options.scales.x.min = moment(chartsStartDate)
    .startOf('day')
    .valueOf();
  theChart.options.scales.x.max = moment(chartsEndDate)
    .add(1, 'days')
    .startOf('day')
    .valueOf();
}

function datetimeAndValueToXandY(point) {
  return {
    x: point.datetime,
    y: point.value,
  };
}

function updateForecastedGenerationChart(chartDataJson) {
  console.count('updateForecastedGenerationChart');
  const chart = Chart.getChart(DAY_AHEAD_FORECAST_SOLAR_WIND_CHART_CANVAS_ID);
  chart.data.datasets = Object.keys(chartDataJson)
    .map((key) => {
      const generation = chartDataJson[key];
      return {
        label: generation.psr_type_human_readable ?? 'Unknown',
        data: generation.points.map(datetimeAndValueToXandY),
        backgroundColor: PSR_COLOR_MAP[generation.psr_type].color,
        borderColor: PSR_COLOR_MAP_DARKER[generation.psr_type].color,
        interpolate: true,
      };
    });
  scaleChart(chart);
  chart.options.plugins.title.text = `Forecasted generation from ${startDateFormatted} to ${endDateFormatted}`;
  chart.update();
}

function updateForecastedTotalLoadChart(chartDataJson) {
  console.count('updateForecastedTotalLoadChart');
  const chart = Chart.getChart(DAY_AHEAD_FORECAST_TOTAL_LOAD_CHART_CANVAS_ID);
  chart.data.datasets = [
    {
      label: 'Forecasted',
      data: chartDataJson.forecastedLoad.points.map(datetimeAndValueToXandY),
    },
    {
      label: 'Actual',
      data: chartDataJson.actualLoad.points.map(datetimeAndValueToXandY),
    },
  ];
  scaleChart(chart);
  chart.options.plugins.title.text = `Forecasted total load from ${startDateFormatted} to ${endDateFormatted}`;
  chart.update();
}

function updateCurrentGenerationChart(chartDataJson) {
  console.count('updateCurrentGenerationChart');
  const chart = Chart.getChart(ACTUAL_GENERATION_CHART_CANVAS_ID);
  chart.data.datasets = Object.keys(chartDataJson)
    .map((key) => {
      const generation = chartDataJson[key];
      return {
        label: generation.psr_type_human_readable ?? 'Unknown',
        data: generation.points.map(datetimeAndValueToXandY),
        hidden: !([
          PSR_TYPES.SOLAR,
          PSR_TYPES.WIND_OFFSHORE,
          PSR_TYPES.WIND_ONSHORE,
        ].includes(generation.psr_type)),
        backgroundColor: PSR_COLOR_MAP[generation.psr_type].color,
        borderColor: PSR_COLOR_MAP_DARKER[generation.psr_type].color,
      };
    });
  // .map((key) => generationDataJsonToChartPoints(chartDataJson[key], true));
  scaleChart(chart);
  chart.options.plugins.title.text = `Actual generation per production type from ${startDateFormatted} to ${endDateFormatted}`;
  chart.update();
}

function updateRenewablePercentageChart(chartDataJson) {
  console.count('updateRenewablePercentageChart');
  const chart = Chart.getChart(RENEWABLE_PERCENTAGE_CHART_CANVAS_ID);
  chart.data.datasets = [
    {
      label: 'Forecasted renewable percentage',
      data: chartDataJson.map(datetimeAndValueToXandY),
    },
  ];
  scaleChart(chart);
  chart.options.plugins.title.text = `Forecasted percentage of renewable production from ${startDateFormatted} to ${endDateFormatted}`;
  chart.update();
}

async function loadForecastedSolarWindChartData() {
  console.count('loadForecastedSolarWindChartData');
  dayAheadForecastSolarWindChartContainer.find('.loading')
    .removeClass('d-none');
  dayAheadForecastSolarWindChartContainer.find('.alert')
    .addClass('d-none');
  const dayAheadForecastURL = new URL(dayAheadForecastSolarWindChartContainer.data('url'));
  console.debug('dayAheadForecastURL', dayAheadForecastURL);
  try {
    const dayAheadForecastSolarWindChartData = await $.ajax({
      url: `${dayAheadForecastURL}?start_date=${chartsStartDate}&end_date=${chartsEndDate}`,
      type: 'GET',
      dataType: 'json',
    });
    console.debug('dayAheadForecastSolarWindChartData', dayAheadForecastSolarWindChartData);
    updateForecastedGenerationChart(dayAheadForecastSolarWindChartData.forecasted_generation);
  } catch (e) {
    console.error(e);
    dayAheadForecastSolarWindChartContainer.find('.alert')
      .text(`An error occurred: ${e.statusText}`)
      .removeClass('d-none');
  } finally {
    dayAheadForecastSolarWindChartContainer.find('.loading')
      .addClass('d-none');
  }
}

async function loadForecastedTotalLoadChartData() {
  console.count('loadForecastedTotalLoadChartData');
  dayAheadForecastTotalLoadChartContainer.find('.loading')
    .removeClass('d-none');
  dayAheadForecastTotalLoadChartContainer.find('.alert')
    .addClass('d-none');
  const dayAheadForecastTotalLoadURL = new URL(dayAheadForecastTotalLoadChartContainer.data('url'));
  const actualTotalLoadURL = new URL(dayAheadForecastTotalLoadChartContainer.data('url-actual'));
  console.debug('dayAheadForecastTotalLoadURL', dayAheadForecastTotalLoadURL);
  console.debug('actualTotalLoadURL', actualTotalLoadURL);
  try {
    const dayAheadForecastTotalLoadChartData = await $.ajax({
      url: `${dayAheadForecastTotalLoadURL}?start_date=${chartsStartDate}&end_date=${chartsEndDate}`,
      type: 'GET',
      dataType: 'json',
    });
    const actualTotalLoadChartData = await $.ajax({
      url: `${actualTotalLoadURL}?start_date=${chartsStartDate}&end_date=${chartsEndDate}`,
      type: 'GET',
      dataType: 'json',
    });
    console.debug('dayAheadForecastTotalLoadChartData', dayAheadForecastTotalLoadChartData);
    console.debug('actualTotalLoadChartData', actualTotalLoadChartData);
    const data = {
      forecastedLoad: dayAheadForecastTotalLoadChartData.forecasted_load.total_load,
      actualLoad: actualTotalLoadChartData.actual_load.total_load,
    };
    updateForecastedTotalLoadChart(data);
  } catch (e) {
    console.error(e);
    dayAheadForecastTotalLoadChartContainer.find('.alert')
      .text(`An error occurred: ${e.statusText}`)
      .removeClass('d-none');
  } finally {
    dayAheadForecastTotalLoadChartContainer.find('.loading')
      .addClass('d-none');
  }
}

async function loadActualGenerationChartData() {
  console.count('loadActualGenerationChartData');
  actualGenerationChartContainer.find('.loading')
    .removeClass('d-none');
  actualGenerationChartContainer.find('.alert')
    .addClass('d-none');
  const actualGenerationURL = new URL(actualGenerationChartContainer.data('url'));
  console.debug('actualGenerationURL', actualGenerationURL);
  try {
    const actualGenerationChartData = await $.ajax({
      url: `${actualGenerationURL}?start_date=${chartsStartDate}&end_date=${chartsEndDate}`,
      type: 'GET',
      dataType: 'json',
    });
    console.debug('actualGenerationChartData', actualGenerationChartData);
    updateCurrentGenerationChart(actualGenerationChartData.generation_per_production_type);
  } catch (e) {
    console.error(e);
    actualGenerationChartContainer.find('.alert')
      .text(`An error occurred: ${e.statusText}`)
      .removeClass('d-none');
  } finally {
    actualGenerationChartContainer.find('.loading')
      .addClass('d-none');
  }
}

async function loadRenewablePercentageChartData() {
  console.count('loadActualGenerationChartData');
  renewablePercentageChartContainer.find('.loading')
    .removeClass('d-none');
  renewablePercentageChartContainer.find('.alert')
    .addClass('d-none');
  const renewablePercentageURL = new URL(renewablePercentageChartContainer.data('url'));
  console.debug('renewablePercentageURL', renewablePercentageURL);
  try {
    const renewablePercentageChartData = await $.ajax({
      url: `${renewablePercentageURL}?start_date=${chartsStartDate}&end_date=${chartsEndDate}`,
      type: 'GET',
      dataType: 'json',
    });
    console.debug('renewablePercentageChartData', renewablePercentageChartData);
    updateRenewablePercentageChart(renewablePercentageChartData.forecasted_renewable_percentage);
  } catch (e) {
    console.error(e);
    renewablePercentageChartContainer.find('.alert')
      .text(`An error occurred: ${e.statusText}`)
      .removeClass('d-none');
  } finally {
    renewablePercentageChartContainer.find('.loading')
      .addClass('d-none');
  }
}

async function handleDatesChanged() {
  console.count('handleDatesChanged');

  const chartStartDatePicker = $('#chartsStartDate');
  const chartEndDatePicker = $('#chartsEndDate');
  const datePickerButtons = $('.date-picker-button');

  console.log(datePickerButtons);

  // Disable inputs
  chartStartDatePicker.prop('disabled', true);
  chartEndDatePicker.prop('disabled', true);
  datePickerButtons.prop('disabled', true);
  chartsStartDate = chartStartDatePicker.val();
  chartsEndDate = chartEndDatePicker.val();

  updateChartDatesFormatted();

  console.debug('chartsStartDate', chartsStartDate);
  console.debug('chartsEndDate', chartsEndDate);

  Promise.all([
    loadForecastedSolarWindChartData(),
    loadForecastedTotalLoadChartData(),
    // loadActualGenerationChartData(),
    loadRenewablePercentageChartData(),
  ])
    .finally(() => {
      chartStartDatePicker.prop('disabled', false);
      chartEndDatePicker.prop('disabled', false);
      datePickerButtons.prop('disabled', false);
    });
}

$(document)
  .ready(async () => {
    console.debug('Document ready');

    dayAheadForecastSolarWindChartContainer = $(`#${DAY_AHEAD_FORECAST_SOLAR_WIND_CHART_CONTAINER_ID}`);
    dayAheadForecastTotalLoadChartContainer = $(`#${DAY_AHEAD_FORECAST_TOTAL_LOAD_CHART_CONTAINER_ID}`);
    actualGenerationChartContainer = $(`#${ACTUAL_GENERATION_CHART_CONTAINER_ID}`);
    renewablePercentageChartContainer = $(`#${RENEWABLE_PERCENTAGE_CHART_CONTAINER_ID}`);

    dayAheadForecastSolarWindChartCanvas = $(`#${DAY_AHEAD_FORECAST_SOLAR_WIND_CHART_CANVAS_ID}`);
    dayAheadForecastTotalLoadChartCanvas = $(`#${DAY_AHEAD_FORECAST_TOTAL_LOAD_CHART_CANVAS_ID}`);
    actualGenerationChartCanvas = $(`#${ACTUAL_GENERATION_CHART_CANVAS_ID}`);
    renewablePercentageChartCanvas = $(`#${RENEWABLE_PERCENTAGE_CHART_CANVAS_ID}`);

    renderDayAheadForecastSolarWindChart();
    renderDayAheadForecastTotalLoadChart();
    renderActualGenerationChart();
    renderRenewablePercentageChart();

    const chartDatePickers = $('.chart-date-picker');
    const today = moment()
      .format('YYYY-MM-DD');

    console.debug(chartDatePickers);

    $('#updateDatesBtn').on('click', () => {
      handleDatesChanged();
    });

    for (const datePickerDOM of chartDatePickers) {
      const datePicker = $(datePickerDOM);
      datePicker.attr('max', today);
      datePicker.val(today);

      const previousDayBtn = datePicker.prop('id') === 'chartsStartDate' ? $('#previousDayStartButton') : $('#previousDayEndButton');
      previousDayBtn.on('click', async () => {
        const currentValue = datePicker.val();
        const newValue = moment(currentValue)
          .subtract(1, 'day')
          .format('YYYY-MM-DD');
        datePicker.val(newValue);
        dayAheadForecastSolarWindChartContainer.find('.loading')
          .show();
        dayAheadForecastTotalLoadChartContainer.find('.loading')
          .show();
        actualGenerationChartContainer.find('.loading')
          .show();
        await handleDatesChanged();
      });

      const nextDayBtn = datePicker.prop('id') === 'chartsStartDate' ? $('#nextDayStartButton') : $('#nextDayEndButton');
      nextDayBtn.on('click', async () => {
        const currentValue = datePicker.val();
        const newValue = moment(currentValue)
          .add(1, 'day')
          .format('YYYY-MM-DD');
        datePicker.val(newValue);
        dayAheadForecastSolarWindChartContainer.find('.loading')
          .show();
        dayAheadForecastTotalLoadChartContainer.find('.loading')
          .show();
        actualGenerationChartContainer.find('.loading')
          .show();
        await handleDatesChanged();
      });
    }

    await handleDatesChanged();
  });
