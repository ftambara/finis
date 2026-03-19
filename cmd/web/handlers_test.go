package main

import (
	"context"
	"encoding/base64"
	"html/template"
	"maps"
	"net/http"
	"net/http/httptest"
	"slices"
	"strings"
	"sync"
	"testing"

	"github.com/alexedwards/scs/v2"
	"github.com/alexedwards/scs/v2/memstore"
	"github.com/ftambara/finis/internal/htmltest"
)

const SessionCookieName = "session"

type StubUserStore struct {
	users  map[UserID]*User
	nextID int32
	mu     sync.Mutex
}

var _ UserStore = (*StubUserStore)(nil)

func NewStubUserStore() *StubUserStore {
	return &StubUserStore{
		users:  make(map[UserID]*User),
		nextID: 1,
	}
}

func (s *StubUserStore) Create(ctx context.Context, email string, password string) (*User, error) {
	// Uncomfortable: Must use the entity constructor on every store implementation.
	s.mu.Lock()
	defer s.mu.Unlock()
	user := &User{ID: s.getNextID(), Email: email, Password: password}
	s.users[user.ID] = user
	return user, nil
}

func (s *StubUserStore) All(ctx context.Context) ([]*User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return slices.Collect(maps.Values(s.users)), nil
}

func (s *StubUserStore) FetchByID(ctx context.Context, id UserID) (*User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	user, ok := s.users[id]
	if !ok {
		return nil, ErrUserNotFound
	}
	return user, nil
}

func (s *StubUserStore) getNextID() UserID {
	id := s.nextID
	s.nextID++
	return id
}

func TestRegistrationGet(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/register", http.NoBody)
	res := httptest.NewRecorder()

	tmpl := template.Must(parseTemplate("register.html.tmpl"))
	RegistrationGet(tmpl)(res, req)

	document := htmltest.ParseHTMLResponse(t, res)

	emailNode := htmltest.GetOne(t, document, "input#user-email")
	htmltest.AssertAttrEquals(t, emailNode, "type", "email")
	htmltest.AssertAttrPresent(t, emailNode, "required")

	passwordNode := htmltest.GetOne(t, document, "input#user-password")
	htmltest.AssertAttrEquals(t, passwordNode, "type", "password")
	htmltest.AssertAttrPresent(t, passwordNode, "required")

	passwordConfirmationNode := htmltest.GetOne(t, document, "input#user-password-confirmation")
	htmltest.AssertAttrEquals(t, passwordConfirmationNode, "type", "password")
	htmltest.AssertAttrPresent(t, passwordConfirmationNode, "required")
}

type stubSessionMiddleware struct {
	Session *scs.SessionManager
}

func newStubSessionMiddleware() *stubSessionMiddleware {
	session := scs.New()
	session.Store = memstore.New()
	return &stubSessionMiddleware{Session: session}
}

func (m *stubSessionMiddleware) Then(next http.Handler) http.Handler {
	return m.Session.LoadAndSave(next)
}

func TestAccountsCreate(t *testing.T) {
	// TODO(ftambara): Test password strength.
	t.Run("can create a valid user", func(t *testing.T) {
		ctx := context.Background()

		userStore := NewStubUserStore()

		userForm := UserCreateForm{Email: "email", Password: "secret", PasswordConfirmation: "secret"}
		form, err := userForm.EncodeForm()
		if err != nil {
			t.Fatalf("failed to marshal user to form: %v", err)
		}

		req := httptest.NewRequest(http.MethodPost, "/register", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		res := httptest.NewRecorder()

		middle := newStubSessionMiddleware()
		tmpl := template.Must(parseTemplate("register.html.tmpl"))
		middle.Then(AccountsCreate(tmpl, userStore, middle.Session)).ServeHTTP(res, req)

		// Assert the response asks for a redirection.
		if res.Code != http.StatusSeeOther {
			t.Errorf("got status %v but wanted %v", res.Code, http.StatusSeeOther)
		}
		wantLocation := "/accounts/verify"
		gotLocation := res.Header().Get("Location")
		if gotLocation != wantLocation {
			t.Errorf("got location header value %v, wanted %v", gotLocation, wantLocation)
		}

		token := assertSessionCookie(t, res.Result())

		// Assert the email has been sent.
		// ...

		// Assert the user has been created correctly
		if len(userStore.users) != 1 {
			t.Fatalf("got %d user in the store, want %v", len(userStore.users), 1)
		}

		var expectedUserID UserID = 1
		created, err := userStore.FetchByID(ctx, expectedUserID)
		if err != nil {
			t.Fatalf("error looking for user with id %d", expectedUserID)
		}

		expected := User{
			ID:    expectedUserID,
			Email: userForm.Email,
			// TODO(ftambara): Stop storing plain-text passwords.
			Password: userForm.Password,
		}
		if *created != expected {
			t.Errorf("created user: %+v, expected:  %+v", created, expected)
		}

		assertUserIDInSession(t, middle.Session, token, expectedUserID)
	})
}

// assertSessionCookie checks that the session has been set, and it was linked to the right account.
//
// Returns the token string.
func assertSessionCookie(t *testing.T, res *http.Response) string {
	t.Helper()

	cookies := res.Cookies()
	if len(cookies) != 1 {
		t.Fatalf("got %d cookies, want %d", len(cookies), 1)
	}
	tokenCookie := cookies[0]
	if tokenCookie.Name != SessionCookieName {
		t.Fatalf("wanted token cookie name to be '%s', got '%s'", SessionCookieName, tokenCookie.Name)
	}
	sessionTokenBytes := len(decodeSessionToken(t, tokenCookie.Value))
	if sessionTokenBytes != SessionTokenBytes {
		t.Errorf("session token length was %d, want %d", sessionTokenBytes, SessionTokenBytes)
	}

	return tokenCookie.Value
}

func decodeSessionToken(t *testing.T, encoded string) []byte {
	t.Helper()

	decoded, err := base64.RawURLEncoding.DecodeString(encoded)
	if err != nil {
		t.Fatalf("error decoding session token: %v", err)
	}
	return decoded
}

func assertUserIDInSession(t *testing.T, sm *scs.SessionManager, token string, expectedID UserID) {
	t.Helper()

	ctx, err := sm.Load(context.Background(), token)
	if err != nil {
		t.Fatalf("error finding session in store: %v", err)
	}
	got := sm.GetInt32(ctx, SessionKeyUserID)
	if got != expectedID {
		t.Errorf("got user ID %d from session, wanted %d", got, expectedID)
	}
}
