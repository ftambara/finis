package main

import (
	"context"
	"html/template"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
)

var projectRoot string
var templateDir string

func init() {
	// Initialize project directory variables.
	mainDir, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	projectRoot = filepath.Dir(filepath.Dir(mainDir))
	templateDir = filepath.Join(projectRoot, "templates")
}

func parseTemplate(filename string) (*template.Template, error) {
	base := filepath.Join(templateDir, "base.html.tmpl")
	tmplPath := filepath.Join(templateDir, filename)
	return template.ParseFiles(base, tmplPath)
}

func main() {
	ctx := context.Background()

	err := run(ctx, ":8000")
	if err != nil {
		log.Fatal(err)
	}
}

func run(ctx context.Context, address string) error {
	// TODO(ftambara): Protect against CSRF/CORF. Ideally, add a test.

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

func home(w http.ResponseWriter, req *http.Request) {
	w.Write([]byte("Hello world"))
}

func NewMultiplexer() *http.ServeMux {
	tmpl := template.Must(parseTemplate("signup.html.tmpl"))
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", home)
	mux.HandleFunc("GET /sign-up", SignUpGet(tmpl))
	return mux
}
