package server

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

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
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	srv := New(":9999", reg, logger)

	if srv.httpServer.Addr != ":9999" {
		t.Errorf("expected :9999, got %s", srv.httpServer.Addr)
	}

	if srv.httpServer.Handler == nil {
		t.Error("handler should not be nil")
	}
}

func TestServerShutdown(t *testing.T) {
	reg := prometheus.NewRegistry()
	logger := slog.New(slog.NewTextHandler(io.Discard, nil)) 
	srv := New(":0", reg, logger) 

	ctx, cancel := context.WithCancel(context.Background())

	errCh := make(chan error, 1)
	go func() {
		errCh <- srv.ListenAndServe(ctx)
	}()


	time.Sleep(100 * time.Millisecond)


	cancel()


	select {
	case err := <-errCh:
		if err != nil && err.Error() != "http: Server closed" {
			t.Errorf("unexpected error: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Error("server did not shut down in time")
	}
}