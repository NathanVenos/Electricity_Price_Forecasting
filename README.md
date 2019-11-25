# Electricity_Price_Forecasting
Predicting hourly electricity prices for the Pepco zone up to a day in advance to inform optimal times for consuming electricity and purchasing strategies.  
  
Notes:  
The area of focus is Node: 51298; Zone: PEPCO, PEP; Interface: BC/PEP; Region: MIDATL  
  
**Weather Forecasts** are available for 7 days. Historical data is also available, but not the historical forecasts, so historical time series analysis will have the unfair/unrealistic advatage of access to ground truth information.  
  
**Day-Ahead LMPs** post by 1:30 PM on the previous day at:  
https://marketsgateway.pjm.com/marketsgateway/pages/secure#!Public/Market_Results_Energy/Market_Prices  
These LMPs are provided as Congestion, Marginal Loss and Total, so the System Energy price must be calculated as Total - Cong - Loss. **Need to note that the timing means real-time forecasts beyond the current day cannot occur until after 1:30pm**  
  
**Seven-Day Load Forecasts** are generated every 30 minutes ~XX:15 & ~XX:45, and retain the forecasts for all hours of a given day until the next day. Historical Forecasts only include data for Market Regions not zones.  
  
Metered **Hourly Load** at the Zone-level is delayed 2 days and is published every morning, so the forecasted load needs to be used beyond then. Preliminary Hourly Load is only delayed by a day, but is only aggregated at the Market Region not Zone level. Adjustments can occur up to 90 days after a given day.  
  
**Generator Outages** are forecasted out 7 days by type () and out 90 days without type.  
  
**Day Ahead Interface Limits** are provided on the same timeline as Day Ahead LMPs.
  
Solar Generation isn't forecast, but cloud cover/visibility as well as sunset/sunrise information is provided in the weather data, and NOAA has calculators to determine. I got access to historical DC irradiance and the expected future irradiance, which could be used along with cloud weather features to make an actionable prediction for ***irradiance*** to use as an additional feature.  
  
Projected Operations Summary datasets only project values for the given day which complicate the ability to forecast into tomorrow, but could be used for a forecasts within the same day, or at least the Projected Peak Datetime could be assumed as the same as the previous day. This data seems dubious, but possibly helpful.  
  
Scheduled Generation is published at 5pm the following day so it isn't forecast. Similarly Real-Time Scheduled Interchange is published the following morning at 7:30am. 
