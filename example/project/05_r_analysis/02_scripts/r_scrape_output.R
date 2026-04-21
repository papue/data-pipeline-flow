library(htmlwidgets)
library(plotly)
library(rvest)

# Read previously scraped HTML file
page <- read_html("../01_input/r_scraped_page.html")
tbl <- html_table(html_element(page, "table"))

# Build interactive chart
fig <- plot_ly(tbl, x = ~year, y = ~value, type = "scatter", mode = "lines")

# Save interactive widget to HTML
out_html <- "../03_output/r_interactive_chart.html"
saveWidget(fig, file = out_html, selfcontained = TRUE)

# Also write a plain HTML report via writeLines
report_lines <- c("<html><body>", "<h1>Scrape summary</h1>",
                  paste0("<p>Rows: ", nrow(tbl), "</p>"), "</body></html>")
writeLines(report_lines, "../03_output/r_scrape_report.html")
