# FILE: R/prediction.R
#
# Trains a simple Linear Regression model on the historical parking
# data and predicts the occupancy percentage for a new set of inputs.
#
# Flask calls this script like:
#   Rscript R/prediction.R "Monday" "11:00" "Normal" "Yes" "Block A"
#
# Arguments (in this order):
#   1. day            e.g. "Monday"
#   2. time           e.g. "11:00"
#   3. weather        e.g. "Normal" / "Rainy" / "Hot"
#   4. event          e.g. "Yes" / "No"
#   5. parking_area   e.g. "Block A"
#
# The script prints ONE line of JSON to stdout, e.g.:
#   {"predicted_occupancy":84.2,"total_slots":100,"predicted_available":16,"status":"HIGH"}
#
# Flask (in app.py) captures this JSON and returns it to the browser.

suppressMessages({
  library(dplyr)
})

source("R/preprocessing.R")

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 5) {
  stop("Usage: Rscript prediction.R <day> <time> <weather> <event> <parking_area>")
}

input_day     <- args[1]
input_time    <- args[2]
input_weather <- args[3]
input_event   <- args[4]
input_area    <- args[5]
input_hour    <- as.integer(substr(input_time, 1, 2))

# 1. Load and clean historical data
data <- get_clean_data("database/parking.db")

if (nrow(data) < 5) {
  stop("Not enough historical data to train a prediction model.")
}

# 2. Turn categorical columns into factors so lm() can use them
data$day          <- as.factor(data$day)
data$weather      <- as.factor(data$weather)
data$event        <- as.factor(data$event)
data$parking_area <- as.factor(data$parking_area)

# 3. Train a simple multiple linear regression model:
#    occupancy % explained by hour, day, weather, event, parking area
model <- lm(occupancy_percentage ~ hour + day + weather + event + parking_area, data = data)

# 4. Build a one-row data frame with the new input, matching factor levels
new_point <- data.frame(
  hour = input_hour,
  day = factor(input_day, levels = levels(data$day)),
  weather = factor(input_weather, levels = levels(data$weather)),
  event = factor(input_event, levels = levels(data$event)),
  parking_area = factor(input_area, levels = levels(data$parking_area))
)

# If the user picked a category never seen in training data, fall back safely
if (any(is.na(new_point))) {
  # Use the overall average occupancy as a safe fallback prediction
  predicted <- mean(data$occupancy_percentage)
} else {
  predicted <- predict(model, newdata = new_point)
}

predicted <- max(0, min(100, round(as.numeric(predicted), 1)))

# 5. Work out total slots for the chosen area (use the most common value seen)
area_capacity <- data %>%
  filter(parking_area == input_area) %>%
  summarise(total = round(mean(total_slots)))

total_slots <- if (nrow(area_capacity) > 0 && !is.na(area_capacity$total[1])) {
  as.integer(area_capacity$total[1])
} else {
  as.integer(round(mean(data$total_slots)))
}

predicted_occupied  <- round(total_slots * predicted / 100)
predicted_available <- total_slots - predicted_occupied

status <- if (predicted <= 40) {
  "LOW"
} else if (predicted <= 70) {
  "MEDIUM"
} else {
  "HIGH"
}

result <- list(
  predicted_occupancy = predicted,
  total_slots = total_slots,
  predicted_occupied = predicted_occupied,
  predicted_available = predicted_available,
  status = status
)

# Print as a single-line JSON string (no pretty print, easier for Python to parse)
cat(jsonlite::toJSON(result, auto_unbox = TRUE))
