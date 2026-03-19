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
	"time"

	"github.com/alexedwards/scs/v2"
	"github.com/alexedwards/scs/v2/memstore"
)

const (
	SessionCookieName = "session"
	SessionTokenBytes = 32
)

var (
	projectRoot string
	templateDir string
)

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

	tmpl := template.Must(parseTemplate("register.html.tmpl"))
	userStore := TodoUserStore{}
	sessionCookieConfig := scs.SessionCookie{
		Name:        SessionCookieName,
		Domain:      "", // Set to issuing domain.
		HttpOnly:    true,
		Path:        "/",
		SameSite:    http.SameSiteStrictMode, // Will use Strict until I have a reason to use Lax.
		Secure:      true,
		Partitioned: true,
		Persist:     true,
	}
	session := scs.SessionManager{
		IdleTimeout: 0,              // No inactivity timeout.
		Lifetime:    24 * time.Hour, // Expire the session after this time.
		Store:       memstore.New(), // TODO(ftambara): replace by an external store.
		Cookie:      sessionCookieConfig,
		Codec:       scs.GobCodec{},
		ErrorFunc: func(w http.ResponseWriter, r *http.Request, err error) {
			logger.Error("session manager failed", slog.String("err", err.Error()))
			// TODO(ftambara): Handle error gracefully.
			http.Error(w, "There was a problem reading your session data.", http.StatusInternalServerError)
		},
		HashTokenInStore: true, // Why not.
	}
	mux := NewMultiplexer(tmpl, userStore, &session)

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

func NewMultiplexer(tmpl *template.Template, store UserStore, session *scs.SessionManager) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", home)
	mux.HandleFunc("GET /register", RegistrationGet(tmpl))
	mux.Handle("POST /register", session.LoadAndSave(AccountsCreate(tmpl, store, session)))
	return mux
}

// TODO(ftambara): Replace by persistent version.
type TodoUserStore struct{}

func (t TodoUserStore) Create(ctx context.Context, email string, password string) (*User, error) {
	// TODO implement me
	panic("implement me")
}

func (t TodoUserStore) All(ctx context.Context) ([]*User, error) {
	// TODO implement me
	panic("implement me")
}

func (t TodoUserStore) FetchByID(ctx context.Context, id UserID) (*User, error) {
	// TODO implement me
	panic("implement me")
}
