# FILE: R/data_analysis.R
#
# This is the main analysis script. Flask calls this script using
# subprocess.run(["Rscript", "R/data_analysis.R"]) whenever the
# Analytics page is opened (or refreshed).
#
# What it does:
#   1. Loads and cleans the parking data (from preprocessing.R)
#   2. Computes summary statistics (mean, median, max, min, sd)
#   3. Finds the peak hour, lowest hour, busiest day
#   4. Computes correlation between occupancy and hour
#   5. Generates 4 charts (from visualization.R) into static/images/
#   6. Writes all numeric results to r_results/analysis_results.json
#      so Flask can read them and show them on the Analytics page.
#
# Run manually with:
#   Rscript R/data_analysis.R

suppressMessages({
  library(dplyr)
  library(jsonlite)
})

source("R/preprocessing.R")
source("R/visualization.R")

cat("Loading and cleaning parking data...\n")
data <- get_clean_data("database/parking.db")

if (nrow(data) == 0) {
  stop("No data available in the database. Add some parking records first.")
}

cat("Computing summary statistics...\n")

overall_stats <- list(
  mean_occupancy   = round(mean(data$occupancy_percentage), 1),
  median_occupancy = round(median(data$occupancy_percentage), 1),
  max_occupancy    = round(max(data$occupancy_percentage), 1),
  min_occupancy    = round(min(data$occupancy_percentage), 1),
  sd_occupancy     = round(sd(data$occupancy_percentage), 1),
  total_records    = nrow(data)
)

# Peak / lowest hour (by average occupancy across all records at that hour)
hourly <- data %>%
  group_by(hour) %>%
  summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop") %>%
  arrange(desc(avg_occupancy))

peak_hour   <- hourly$hour[1]
lowest_hour <- hourly$hour[nrow(hourly)]

# Busiest day
daily <- data %>%
  group_by(day) %>%
  summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop") %>%
  arrange(desc(avg_occupancy))
busiest_day <- daily$day[1]

# Correlation between hour of day and occupancy (simple linear relationship check)
correlation_hour_occupancy <- round(cor(data$hour, data$occupancy_percentage), 3)

peak_stats <- list(
  peak_hour = sprintf("%02d:00", peak_hour),
  lowest_hour = sprintf("%02d:00", lowest_hour),
  busiest_day = busiest_day,
  correlation_hour_occupancy = correlation_hour_occupancy
)

cat("Generating charts...\n")
plot_files <- generate_all_plots(data, out_dir = "static/images")

result <- list(
  overall_stats = overall_stats,
  peak_stats = peak_stats,
  plot_files = plot_files,
  generated_at = as.character(Sys.time())
)

dir.create("r_results", showWarnings = FALSE)
write(toJSON(result, auto_unbox = TRUE, pretty = TRUE), "r_results/analysis_results.json")

cat("Analysis complete. Results written to r_results/analysis_results.json\n")
