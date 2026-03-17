package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"testing"
	"time"
)

func waitForReady(
	ctx context.Context,
	timeout time.Duration,
	endpoint string,
) error {
	client := http.Client{}
	startTime := time.Now()
	sleepDuration := 100 * time.Millisecond
	for {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, http.NoBody)
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}
		resp, respErr := client.Do(req)
		if respErr != nil {
			continue
		}
		err = resp.Body.Close()
		if err != nil {
			return fmt.Errorf("failed to close body: %w", err)
		}
		if resp.StatusCode == http.StatusOK {
			fmt.Println("Endpoint is ready.")
			return nil
		}

		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			if time.Since(startTime) >= timeout {
				if respErr != nil {
					fmt.Printf("Error making request: %s\n", respErr)
				}
				return errors.New("timeout reached while waiting for endpoint")
			}
			time.Sleep(sleepDuration)
		}
	}
}

func TestRun(t *testing.T) {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	t.Cleanup(cancel)

	var runErr error
	go func() {
		runErr = run(ctx, ":9658")
	}()
	err := waitForReady(ctx, 1*time.Second, "http://127.0.0.1:9658/")
	if err != nil {
		if runErr != nil {
			fmt.Printf("Error running the server: %s\n", runErr)
		}
		t.Fatal(err)
	}
	if runErr != nil {
		t.Fatal(err)
	}
}

func TestRegistration(t *testing.T) {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	t.Cleanup(cancel)

	var runErr error
	go func() {
		runErr = run(ctx, ":9658")
	}()
	err := waitForReady(ctx, 1*time.Second, "http://127.0.0.1:9658/")
	if err != nil {
		panic(err)
	}
	if runErr != nil {
		panic(runErr)
	}

	client := http.Client{}
	res, err := client.Get("http://127.0.0.1:9658/register")
	if err != nil {
		t.Fatalf("error getting registration page: %v", err)
	}
	if res.StatusCode != http.StatusOK {
		t.Fatalf("registration page status code is not 200 OK: %v", res.StatusCode)
	}

	// Send form
	// ...
}
