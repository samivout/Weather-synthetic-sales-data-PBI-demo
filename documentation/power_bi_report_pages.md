# The Power BI report

The main purpose of the report is to enable the user to analyze patterns in sales quantities and weather conditions. 
The designed audience for the report is an analyst who is moderately familiar with statistics and multidimensional 
visualization.

## The main quantities

The report is focused on enabling the analysis of two quantities: number of sales and what is named as the Weather 
Index. The Weather Index acts as a quantity that reflects how ideal or pleasant the weather. The computation is 
defined in the `synda` Python package's `SimpleWeatherModel` class, but in short it is assumed to be a simple 
function of average temperature of the hour and the accumulated rainfall of the hour. The model has parameters for 
the ideal temperature and a tolerance threshold for rainfall, and temperature deviations from the ideal or exceeding 
the rainfall threshold start reducing the Weather Index value from the ideal 1.0 towards 0.0.

## Slicer selection

The report included two main sets of slicers to filter/aggregate the data, and they are grouped in panels at the top 
of a page and the right edge of the page.

The slicer selection on each page can vary by design so that only relevant slicers are included for each page.

### Regular slicers (Top panel group)

The top panel consists of the following slicers:
- Slicing by year, month and day of month range.
- Slicing by the hour of day range.
- Slicing by location with multiselect. 
- Slicing by Weather Index Bin range.
- Choosing the main sales measure used in visuals.

The time-related slicer are rather evident in functionality, but the more specific slicer here are the Weather Index 
Bin and Measure Name slicer. The first allows the user to filter sales by weather index ranges, thus enabling 
targeted analysis of specific weather condition intervals. The second allows the user to choose the sales 
aggregation type from sum, average, median, max, min, and sdev (this is hourly aggregation).  

### Data aggregation slicers (Right-edge panel group)

The right-edge panel contains slicers that allow the user to further aggregate the data by the given dimensions via the
given aggregation method. These are implemented via Calculation Groups, and they wrap the chosen main measure 
computation into a SUMMARIZECOLUMNS call to compute the value of the main measure for each group created by 
SUMMARIZECOLUMNS, finally aggregating over each group's evaluation by the chosen aggregation type.

These aggregations act as powerful dynamic tools that enable the user to make more fair comparisons of sales across
locations with varying number of personnel or products. The order of the aggregation operations is the same as the 
order of the slicers in the panel counting from top to bottom.

A special remark that should be noted here is that sequentially chained aggregations is not statistically equivalent 
to computing an aggregation over a flattened grouping. For example: it is not equivalent to compute an average of 
the sum of sales first across different products and then across different locations vs. computing the average of 
the sum of sales across all nonzero combinations of locations and products. This is the aspect that takes some 
understanding of statistics from the end-user. Naturally the function of the data aggregation is strongly tied to 
the dimensions being visualized over in a visual. For example, if a visual shows sales over hours of the day, then 
choosing a data aggregation over hours does nothing to the computation for that particular visual.

The given data aggregation dimensions are:
- Product
- Person
- Location
- Weather Index
- Hour
- Date

For each of these dimensions the user can choose the aggregation type from sum, average, median, max, min and sdev. 
Furthermore, there are sales-weighted variations of average, median and sdev available also.

On pages where both temporal and categorical aggregation dimensions are available, the user can use the UI to switch 
between temporal-first and categorical-first ordering of the aggregations.

## The report pages

The report consists of multiple pages with focus on a different analysis aspect. The main idea of each page is 
documented here.

### Main Dashboard

The main dashboard acts as a simple overview to the data. It has visualizations for the sales across locations, 
products, a simple map view, and gauges for the current year sales measure vs previous year, and also current year 
vs average of previous years. Finally, it also has a timeseries visual for location-averaged sales and 
location-averaged Weather Index, inviting the user to analyze the relationship more deeply.

### Location analytics

This page contains a large ribbon chart visualization over a date hierarchy. Together with the top-panel and 
right-panel slicers, this enables a deeper visualization of how locations fare over time against each other.

### Location drill through

The location drill through page allows the user to analyze a particular location's data more deeply. It also has a 
ribbon chart visual, but this time for the personnel of that location. It also has tables for the chosen sales 
measure across year and months and their percentage change, products and their ranks by the chosen measure, and the 
chosen sales measure for each person. 

### Location Sales—Hour correlation

This drill through page allows the user to analyze the correlation of sales with the hour of day. The correlation 
computation is performed on an hour-by-hour basis and the result can be visualized across a date hierarchy. The 
first visual shows a naive correlation between the hour of day itself and sales. The second visual on the other hand 
first computes for each hour the distance to the peak sales hour, and then computes the correlation of that distance 
and sales.

Together these visuals enable the quantitative analysis of how strongly the time of day might affect sales and how 
strongly sales drop off when moving away from peak hours.

### Person drill through

The person drill through page is rather similar to the location drill through page, containing simple sales 
information and ranking at the person level.

### Sales—Weather Correlation

The Sales—Weather Correlation allows the user to quantitatively analyze how sales correlate with weather conditions. 
This page isn't location specific and allows robust analysis of the correlation across all data, aggregated across 
locations, or by single location. The top-panel and right-panel slicers are rather powerful tools on this page.

### Sales—Weatehr Scatter

The Sales—Weatehr Scatter allows the user to visualize how the chosen sales measure and the average daily weather 
index are clustered. Each datapoint in the visual is a particular location's evaluation of the chosen sales measure 
on a single date, visualized against the average weather index of that date and location. This results in a scatter 
plot that can show clustering or regression trends between sales and weather conditions. Furthermore, the user can 
utilize the UI to activate a play axis to further visualize the data hour-by-hour, allowing analysis at an even 
deeper level.

### Sales—Weather—Hour Heatmap

The Sales—Weather—Hour Heatmap is a 2D histogram visualizing the chosen sales measure simultaneously against hour of 
the day (x-axis) and a weather index bin (y-axis). On top of the heatmap is also a bar chart visualization that 
shows the same data but visualized only against the hour of day, while on the right side is another bar chart that 
visualizes the same data against only the Weather Index bin range.

Together with the top-panel and right-panel slicers this visual provides very robust methods to visualize how sales 
are aligned against hours of the day and weather index bin at the same time.

The visulizations on this page were implemented using the third-party Deneb visuals, as the native tooling in Power 
BI simply did not provide sufficient tooling for both visually pleasing and performant implementation of a 2D 
histogram heatmap.

### Sales Decomposition

The Sales Decomposition page contains a single decomposition visual, which allows the user to analyze how the chosen 
sales measure comes together from various different categories. The user can freely decompose the measure in their 
chosen order by using the dimensions from the date hierarchy, hour of day, location, product, person and Weather 
Index Bin range.

Similarly to many of the previous pages, the top-panel and right-panel slicers allow for very intricate 
decomposition of the chose measure at various level of data. The decomposition visual is especially powerful 
together with the Data aggregation slicers as the user can see how the data flows upwards from the lower levels of 
the decomposition towards the upper levels.

### Hypothetical Sales Loss

Finally, the Hypothetical Sales Loss page shows a single timeseries visual across a date hierarchy. The visual 
firstly shows the value of the chosen sales measure. Secondly, it shows a hypothetical percentage loss of sales due 
to non-ideal weather. The computation is quite simple and assumes a direct linear relationship between the weather 
index and sales, and thus makes a comparison of real sales against an idealized what-if scenario if the weather were 
to always be perfect.