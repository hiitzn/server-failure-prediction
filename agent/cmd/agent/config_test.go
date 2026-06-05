package main

import (
    "os"
    "testing"
    "time"
)

func TestLoadConfigDefaults(t *testing.T) {
    cfg, err := loadConfig()
    if err != nil {
        t.Fatalf("loadConfig failed: %v", err)
    }
    
    if cfg.ListenAddr != ":9100" {
        t.Errorf("expected :9100, got %s", cfg.ListenAddr)
    }
    if cfg.ScrapeInterval != 15*time.Second {
        t.Errorf("expected 15s, got %v", cfg.ScrapeInterval)
    }
    if cfg.DiskPath != "/" {
        t.Errorf("expected /, got %s", cfg.DiskPath)
    }
    if cfg.LogLevel != "info" {
        t.Errorf("expected info, got %s", cfg.LogLevel)
    }
}

func TestLoadConfigWithEnv(t *testing.T) {
    os.Setenv("LISTEN_ADDR", ":8080")
    os.Setenv("SCRAPE_INTERVAL", "30s")
    defer func() {
        os.Unsetenv("LISTEN_ADDR")
        os.Unsetenv("SCRAPE_INTERVAL")
    }()
    
    cfg, err := loadConfig()
    if err != nil {
        t.Fatalf("loadConfig failed: %v", err)
    }
    
    if cfg.ListenAddr != ":8080" {
        t.Errorf("expected :8080, got %s", cfg.ListenAddr)
    }
    if cfg.ScrapeInterval != 30*time.Second {
        t.Errorf("expected 30s, got %v", cfg.ScrapeInterval)
    }
}

func TestParseDuration(t *testing.T) {
    d, err := parseDuration("30")
    if err != nil || d != 30*time.Second {
        t.Errorf("parseDuration('30') = %v, want 30s", d)
    }
    
    d, err = parseDuration("1m30s")
    if err != nil || d != 90*time.Second {
        t.Errorf("parseDuration('1m30s') = %v, want 90s", d)
    }
}