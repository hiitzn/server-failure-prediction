package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/prometheus/client_golang/prometheus"

	"github.com/yourname/server-agent/internal/collector"
	"github.com/yourname/server-agent/internal/server"
)

func main() {
	cfg, err := loadConfig()
	if err != nil {
		slog.Error("invalid config", "err", err)
		os.Exit(1)
	}

	logger := buildLogger(cfg.LogLevel)

	if err := run(cfg, logger); err != nil {
		logger.Error("agent exited with error", "err", err)
		os.Exit(1)
	}
}

// run contains the real startup logic, separated from main() for testability.
func run(cfg Config, logger *slog.Logger) error {
	// Isolated registry keeps our metrics separate from the default one.
	reg := prometheus.NewRegistry()

	gauges, err := collector.NewGauges(reg)
	if err != nil {
		return err
	}

	sys := collector.NewSystemCollector(cfg.DiskPath)
	scraper := collector.NewScraper(sys, gauges, cfg.ScrapeInterval, logger)

	srv := server.New(cfg.ListenAddr, reg, logger)

	// Cancel the context on SIGINT / SIGTERM for a clean shutdown.
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Run the scrape loop in the background.
	go scraper.Run(ctx)

	// Block until the HTTP server exits (triggered by ctx cancellation).
	return srv.ListenAndServe(ctx)
}

func buildLogger(level string) *slog.Logger {
	var l slog.Level
	if err := l.UnmarshalText([]byte(level)); err != nil {
		l = slog.LevelInfo
	}
	return slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: l}))
}
