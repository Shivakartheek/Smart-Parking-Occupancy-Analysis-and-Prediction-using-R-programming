# FILE: R/visualization.R
#
# Generates the static analysis charts (PNG images) shown on the
# Analytics page. These are made with ggplot2, saved into
# static/images/, and then simply displayed as <img> tags by Flask.
#
# This file is sourced by R/data_analysis.R - it is not meant to be
# run on its own.

suppressMessages({
  library(ggplot2)
  library(dplyr)
})

# 1. Occupancy vs Time (average occupancy % for each hour of the day)
plot_occupancy_vs_time <- function(data, out_dir) {
  hourly <- data %>%
    group_by(hour) %>%
    summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop")

  p <- ggplot(hourly, aes(x = hour, y = avg_occupancy)) +
    geom_line(color = "#2563eb", linewidth = 1.2) +
    geom_point(color = "#2563eb", size = 2.5) +
    labs(title = "Average Occupancy by Hour of Day",
         x = "Hour", y = "Average Occupancy (%)") +
    theme_minimal(base_size = 13)

  ggsave(file.path(out_dir, "occupancy_vs_time.png"), p, width = 7, height = 4.2, dpi = 120)
}

# 2. Occupancy by Day of week
plot_occupancy_by_day <- function(data, out_dir) {
  day_levels <- c("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
  daily <- data %>%
    group_by(day) %>%
    summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop") %>%
    mutate(day = factor(day, levels = day_levels))

  p <- ggplot(daily, aes(x = day, y = avg_occupancy, fill = day)) +
    geom_col(show.legend = FALSE) +
    labs(title = "Average Occupancy by Day of Week",
         x = "Day", y = "Average Occupancy (%)") +
    theme_minimal(base_size = 13) +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))

  ggsave(file.path(out_dir, "occupancy_by_day.png"), p, width = 7, height = 4.2, dpi = 120)
}

# 3. Parking Area Comparison
plot_area_comparison <- function(data, out_dir) {
  area <- data %>%
    group_by(parking_area) %>%
    summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop")

  p <- ggplot(area, aes(x = parking_area, y = avg_occupancy, fill = parking_area)) +
    geom_col(show.legend = FALSE) +
    labs(title = "Average Occupancy by Parking Area",
         x = "Parking Area", y = "Average Occupancy (%)") +
    theme_minimal(base_size = 13)

  ggsave(file.path(out_dir, "area_comparison.png"), p, width = 7, height = 4.2, dpi = 120)
}

# 4. Event vs Non-Event Occupancy
plot_event_vs_occupancy <- function(data, out_dir) {
  ev <- data %>%
    group_by(event) %>%
    summarise(avg_occupancy = mean(occupancy_percentage), .groups = "drop")

  p <- ggplot(ev, aes(x = event, y = avg_occupancy, fill = event)) +
    geom_col(show.legend = FALSE, width = 0.5) +
    labs(title = "Event Day vs Normal Day Occupancy",
         x = "Event Happening?", y = "Average Occupancy (%)") +
    theme_minimal(base_size = 13)

  ggsave(file.path(out_dir, "event_vs_occupancy.png"), p, width = 7, height = 4.2, dpi = 120)
}

# Runs all four plots and returns their file names.
generate_all_plots <- function(data, out_dir = "static/images") {
  dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
  plot_occupancy_vs_time(data, out_dir)
  plot_occupancy_by_day(data, out_dir)
  plot_area_comparison(data, out_dir)
  plot_event_vs_occupancy(data, out_dir)

  c("occupancy_vs_time.png", "occupancy_by_day.png",
    "area_comparison.png", "event_vs_occupancy.png")
}
