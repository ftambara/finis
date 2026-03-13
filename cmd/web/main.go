package main

import (
	"context"
	"log"
	"net/http"
	"os/signal"
	"syscall"
)

func home(w http.ResponseWriter, req *http.Request) {
	w.Write([]byte("Hello world"))
}

func run(ctx context.Context, address string) error {
	ctx, cancel := signal.NotifyContext(ctx, syscall.SIGINT)
	defer cancel()

	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", home)
	var listenErr error
	go func() {
		listenErr = http.ListenAndServe(address, mux)
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
