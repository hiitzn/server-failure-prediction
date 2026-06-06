package server

import (
    "io"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/prometheus/client_golang/prometheus"
)

func TestHealthzHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/healthz", nil)
    w := httptest.NewRecorder()
    
    healthzHandler(w, req)
    
    resp := w.Result()
    body, _ := io.ReadAll(resp.Body)
    
    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected 200, got %d", resp.StatusCode)
    }
    if string(body) != "ok" {
        t.Errorf("expected 'ok', got %s", string(body))
    }
}

func TestNewServer(t *testing.T) {
    reg := prometheus.NewRegistry()
    
    srv := New(":9999", reg, nil)
    
    if srv.httpServer.Addr != ":9999" {
        t.Errorf("expected :9999, got %s", srv.httpServer.Addr)
    }
    if srv.httpServer.Handler == nil {
        t.Error("handler should not be nil")
    }
}