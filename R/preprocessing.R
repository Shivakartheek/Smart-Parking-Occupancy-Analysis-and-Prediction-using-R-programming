# FILE: R/preprocessing.R
#
# Shared helper functions for reading and cleaning parking data.
# This file is "sourced" (imported) by data_analysis.R and prediction.R
# so we don't repeat the same code in every script.

suppressMessages({
  library(DBI)
  library(RSQLite)
  library(dplyr)
})

# Reads all rows from the SQLite database into an R data frame.
# db_path: path to database/parking.db (relative to project root)
load_parking_data <- function(db_path = "database/parking.db") {
  con <- dbConnect(RSQLite::SQLite(), db_path)
  data <- dbGetQuery(con, "SELECT * FROM parking_data")
  dbDisconnect(con)
  data
}

# Basic cleaning:
#  - removes rows with missing values
#  - removes impossible rows (occupied > total, negative numbers)
#  - recalculates occupancy_percentage to make sure it is always correct
#  - converts hour-of-day into a numeric column for analysis
clean_parking_data <- function(data) {
  data <- data %>%
    filter(!is.na(total_slots), !is.na(occupied_slots)) %>%
    filter(total_slots > 0, occupied_slots >= 0, occupied_slots <= total_slots) %>%
    mutate(
      occupancy_percentage = round((occupied_slots / total_slots) * 100, 1),
      hour = as.integer(substr(time, 1, 2))
    )
  data
}

# Adds a "status" column (LOW / MEDIUM / HIGH) based on occupancy %,
# using the same thresholds as the Flask backend.
classify_status <- function(data) {
  data %>%
    mutate(status = case_when(
      occupancy_percentage <= 40 ~ "LOW",
      occupancy_percentage <= 70 ~ "MEDIUM",
      TRUE ~ "HIGH"
    ))
}

# Convenience function: load + clean + classify in one call.
get_clean_data <- function(db_path = "database/parking.db") {
  load_parking_data(db_path) %>%
    clean_parking_data() %>%
    classify_status()
}
