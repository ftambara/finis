package main

import (
	"context"
	"log"
	"net/http"
)

func home(w http.ResponseWriter, req *http.Request) {
	w.Write([]byte("Hello world"))
}

func run(ctx context.Context, address string) error {
	// TODO(ftambara): Close context on interrupt/stop signals
	// TODO(ftambara): Change this so we can work with httptest.NewServer

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
