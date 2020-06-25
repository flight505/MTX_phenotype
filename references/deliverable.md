The task is just coding a Streamlit app that can identify people with several diagnoses. 

* The math behind a diagnosis such as Neutropenia would be any patient with white blood cells <0.5x10 ^ 9 / L for over ten days. 
* I need sliders for every diagnosis - there are six different diagnoses. 
* As there are several diagnoses, I need st.checkbox for every diagnosis so I can check for multiple at the same time. 
* You also need to transform the test data set; there is some time series from when the blood samples were taken - nothing big. 
* Some basic statistics, how many patients have the checked diagnoses. 
* A pull-down where the detected patients can be plotted - standard plotly scatter plots of the data points in the diagnoses and if multiple are checked either overlaying plots or only individual would be fine. 