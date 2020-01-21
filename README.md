# Electricity Price Forecasting
  
**Project Rationale:** Large consumers of electricity could realize significant savings if they could identify upcoming electricity prices and shift their usage from a more expensive time to a cheaper one (e.g. re-schedule an electricity-intensive industrial process), or simply reduce usage during particularly expensive times (e.g. temporarily relaxing thermostat set points).
  
**Presentation Link:** https://docs.google.com/presentation/d/1QpDn5O5K5aPH0gkn6Ox9qHGq40Ov6EROQUAUkfl29y4/edit?usp=sharing
  
**Background:** PJM Interconnection (PJM) is the regional transmission operator for the electrical grid in the central portion of the eastern United States. They manage the operations of the grid and its wholesale electricity market. The wholesale electricity market is open to large consumers of electricity as well as utilities and other relevant market participants. The market establishes a price for each hour and for each pre-defined geographic zone such that all electricity usage in a given zone occurring within a given hour is charged the established price, which is called the Locational Marginal Price (LMP), and is comprised of three components: System Energy, Congestion, and Marginal Loss.  
  
The wholesale market has two parts: 1) Participants have the option to buy a specified quantity of electricity on the Day-Ahead market, which operates every afternoon with an established price for each hour of the following day. 2) Participants are charged the Real-Time market's price as established at the end of a given hour for whatever electricity usage they did not purchase on the Day-Ahead market (purchasing more electricity on the Day-Ahead market than is actually used results in a credit for the participant). While the consumer of electricity pays a set price for all usage within a given hour, the electricity generators are compensated based on prices that vary over 5-minute intervals to ensure sufficient market signals for aligning supply and demand in real-time. The generator prices are published publicly every 5-minutes and averaged over the course of the hour to establish the official hourly price charged to consumers.
  
**Data Access:** The project focuses on forecasting prices within the grid's the PEPCO zone (Node 51298), which encompasses Washington, DC and its Maryland suburbs using data from 1/1/2016 through 11/20/2019. This zone is located within the Mid-Atlantic Region of the grid and its BC/PEPCO Interface, which encompasses the areas served by the PEPCO and Baltimore Gas & Electric utilities. Data utilized for the project focuses on these boundaries. Data considered for use as an exogenous regressor was limited to data that has known or publicly available forecasts of its values within the forecast horizon because you can't use data that won't be available in production.
  
PJM publicly hosts various types of non-proprietary data via its Data Miner 2 platform, which allows for .csv formatted downloads via the web portal or requests for .json formatted downloads via its API. Historical data was acquired via the web portal, and AWS' Lambda service is utilized to automate and save hourly API requests, allowing data sets to remain up to date.
  
Weather data for Washington, DC was acquired using the DarkSky API, which provides free access to historical weather data, as well as real-time weather data and forecasts in .json format. They do not store historical weather forecasts, only actuals, so the data used in the modeling includes some leakage because in production you would have to rely on weather forecasts, which are less accurate than actuals. The short forecast horizon of the project (1 and 2 hours ahead) mitigates the leakage, but it exists nonetheless within the historical data. AWS' Lambda service is utilized to automate and save hourly API requests for weather forecasts, eliminating the data leakage issue moving forward. Similarly, PJM publishes PEPCO Load (i.e. instantaneous usage) forecasts every 30 minutes, but does not store them historically, meaning data leakage exists there as well, so AWS' Lambda service is utilized to eliminate that problem moving forward.
  
**Methodology:** The data was compiled and joined using a common time series. The target variable is the hourly Real-Time Locational Marginal Price (RT LMP) for the PEPCO Zone. Stationarity of the Time Series was confirmed using the Augmented Dickey-Fuller test, and autocorrelation of the target variable was inspected. The correlation coefficient drops below 0.50 after 4 hours, and only breaches that threshold again 24 hours prior (i.e. the same time on the previous day), implying autocorrelation is not very significant outside of short time periods.
  
An initial round of feature engineering included: generating more complex weather metrics such as enthalpy, which is a measure of energy in the air, and degree days which measure the absolute difference between an actual and baseline temperature to isolate the impact on heating versus cooling; and the calculate the difference between an Interface's transmission flow and transmission limit. Then an initial round of EDA and feature selection was performed using domain knowledge along with analyzing the correlation between the target and features, and standardizing the target and features then plotting them alongside each other to inspect seasonal patterns and their similarities.
  
The model utilizes a publicly available Time Series Forecasting library called Prophet, which is maintained by Facebook, and is at its core an additive regression model. It decomposes the data set into a trend, annual season, weekly season, daily season, and residuals and then generates and aggregates a regression model for each with Fourier transforms applied to the seasonal data. Forward selection with occasional doubling back was used to select the final assortment of regressors. The regressors included the day-ahead price components, PEPCO load, weather (temperature, humidity, and degree days), BC/PEPCO Interface flow and spread, whether PJM considers and hour on or off peak as well as several engineered interaction, polynomial and lag (i.e. the data point at a time in the past) features based on the day-ahead and historical real-time prices. To stabilize variance and improve the normality of the target distribution, a Yeo-Johnson power transformation of the target was applied, yielding improved performance and better forecasting of outliers. Hyperparameter tuning was performed by iterating through different values, but the defaults ultimately yielded the best results. Cross-validation was used to verify the results. Attempts to model the three components of the LMPs separately yielded slightly poorer results than forecasting the aggregate LMP. Forecasts of the 1-hour-ahead and 2-hour-ahead LMPs are made using separate models with the only difference being that the 2-hour-ahead model does not have the lag variables nearest in the past (i.e. 1 hour ago) because it would not yet exist in production.
  
A parallel project to forecast the PEPCO Zone's Load (i.e. Instantaneous Usage) was also conducted. This time series is more autocorrelated and has a lower variance than the Real-Time LMP, making it easier to accurately forecast. While less actionable than the RT LMP forecast since PJM already performs this forecasting, the better accuracy amounted to a fun and relatively quick side project.
  
**Conclusions:** The success of the project was evaluated using mean absolute percent error (MAPE) and compared to a baseline MAPE of 20.51%, which is the error between the published Day-Ahead LMPs and the actual Real-Time LMPs. When predicting one-hour ahead, the final RT LMP forecasting model had a MAPE of 15.74%, representing 4.77% improvement to MAPE and a mean absolute error that is $1.47 less than baseline. The MAPE of 2-hour-ahead forecast increases to 17.03%, representing $0.51 increase to mean absolute error. For reference, the RT LMP mean is $33.01 and standard deviation is $28.10. 
  
The high variance and relatively frequent occurrence of outliers pose a challenge to the generation of accurate forecasts, particularly since the outliers represent times during which an accurate forecast would yield significant value to consumers shifting electricity usage, so they cannot be ignored. A significant driver of the pricing, and outliers in particular, are driven by unexpected changes to operating conditions within the electrical grid, but limited real-time information on those operations is publicly available making them difficult to accommodate in the model. Additionally, producing accurate time series forecasts of highly competitive markets like this one is very difficult due to the large number of competitors trying to manipulate the market in their favor.
  
The side project's PEPCO Zonal Load Forecast yielded a MAPE of 4.42% for 1-hour-ahead forecasts as compared to the baseline (PJM's published forecast) of 1.56%. And when evaluating over a 7-day forecast horizon of hourly predictions, the MAPE only increases to 4.68% though it had the advantage of using actual weather data as opposed to forecasted weather data as exogenous regressors.
  
**Next Steps:** Some potential next steps include: Integrating real-time data feeds and placing the model into production via AWS. Classifying specific times when a usage shift would be valuable. Solving the problem with a different type of model (e.g. XGBoost or LSTM Neural Network). Identifying additional data sources that could improve the model performance such as PJM's postings of Emergency Procedures.
