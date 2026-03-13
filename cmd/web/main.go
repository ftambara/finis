package main

import (
	"context"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
)

func home(w http.ResponseWriter, req *http.Request) {
	w.Write([]byte("Hello world"))
}

func run(ctx context.Context, address string) error {
	ctx, cancel := signal.NotifyContext(ctx, syscall.SIGINT)
	defer cancel()

	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))

	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", home)

	server := http.Server{
		Addr:     address,
		Handler:  mux,
		ErrorLog: slog.NewLogLogger(logger.Handler(), slog.LevelError),
	}

	logger.Info("starting server", slog.String("addr", address))

	var listenErr error
	go func() {
		listenErr = server.ListenAndServe()
	}()

	<-ctx.Done()
	return listenErr
}

func main() {
	ctx := context.Background()

	err := run(ctx, ":8000")
	if err != nil {
		log.Fatal(err)
	}
}
