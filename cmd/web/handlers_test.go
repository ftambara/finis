package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/xml"
	"html/template"
	"io"
	"maps"
	"net/http"
	"net/http/httptest"
	"slices"
	"strings"
	"sync"
	"testing"

	"github.com/alexedwards/scs/v2"
	"github.com/alexedwards/scs/v2/memstore"
	"github.com/andybalholm/cascadia"
	"golang.org/x/net/html"
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

func (s *StubUserStore) Create(ctx context.Context, Email string, Password string) (*User, error) {
	// Uncomfortable: Must use the entity constructor on every store implementation.
	s.mu.Lock()
	defer s.mu.Unlock()
	user := &User{ID: s.getNextID(), Email: Email, Password: Password}
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

	document := parseHTMLResponse(t, res)

	emailNode := htmlGet(document, "input#user-email")
	assertAttrEquals(t, emailNode, "type", "email")
	assertAttrPresent(t, emailNode, "required")

	passwordNode := htmlGet(document, "input#user-password")
	assertAttrEquals(t, passwordNode, "type", "password")
	assertAttrPresent(t, passwordNode, "required")

	passwordConfirmationNode := htmlGet(document, "input#user-password-confirmation")
	assertAttrEquals(t, passwordConfirmationNode, "type", "password")
	assertAttrPresent(t, passwordConfirmationNode, "required")
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
	sessionTokenBytes := len(decodeSessionToken(tokenCookie.Value))
	if sessionTokenBytes != SessionTokenBytes {
		t.Errorf("session token length was %d, want %d", sessionTokenBytes, SessionTokenBytes)
	}

	return tokenCookie.Value
}

func parseHTMLResponse(t *testing.T, res *httptest.ResponseRecorder) *html.Node {
	if res.Code != http.StatusOK {
		t.Errorf("got status %v but wanted %v", res.Code, http.StatusOK)
	}
	if res.Body.Len() == 0 {
		t.Fatal("received empty response body")
	}
	r := bytes.NewReader(res.Body.Bytes())
	assertHTMLWellFormed(t, r)

	_, err := r.Seek(0, io.SeekStart)
	if err != nil {
		t.Fatalf("error rewinding body reader: %s", err)
	}

	document, err := html.Parse(r)
	if err != nil {
		t.Fatalf("error parssing response body as HTML: %s", err)
	}
	return document
}

func htmlGet(n *html.Node, query string) *html.Node {
	results := htmlQueryAll(n, query)
	if len(results) > 1 {
		panic("too many results")
	} else if len(results) == 0 {
		panic("no results")
	}
	return results[0]
}

func htmlQueryAll(n *html.Node, query string) []*html.Node {
	sel, err := cascadia.Parse(query)
	if err != nil {
		panic(err)
	}
	return cascadia.QueryAll(n, sel)
}

func htmlAttr(n *html.Node, name string) (value string, found bool) {
	for _, attr := range n.Attr {
		if attr.Key == name {
			return attr.Val, true
		}
	}
	return "", false
}

func assertAttrEquals(t *testing.T, n *html.Node, name string, valWant string) {
	t.Helper()
	valGot, found := htmlAttr(n, name)
	if !found {
		t.Errorf("attr %s not found", name)
	}
	if valGot != valWant {
		t.Errorf("attr %s value was %s, expected %s", name, valGot, valWant)
	}
}

func assertAttrPresent(t *testing.T, n *html.Node, name string) {
	t.Helper()
	assertAttrEquals(t, n, name, "")
}

var assertHTMLWellFormed = assertHTMLWellFormedXML

func assertHTMLWellFormedHTML(t *testing.T, buffer io.Reader) {
	t.Helper()

	tokenizer := html.NewTokenizer(buffer)
	for {
		tokenType := tokenizer.Next()
		if tokenType == html.ErrorToken {
			if tokenizer.Err() == io.EOF {
				return // Done, the HTML is valid.
			}
			t.Fatalf("Error parsing HTML: %s", tokenizer.Err())
		}
	}
}

func assertHTMLWellFormedXML(t *testing.T, buffer io.Reader) {
	t.Helper()

	decoder := xml.NewDecoder(buffer)
	decoder.Strict = false
	decoder.AutoClose = xml.HTMLAutoClose
	decoder.Entity = xml.HTMLEntity
	for {
		_, err := decoder.Token()
		switch err {
		case io.EOF:
			return // Done, the HTML is valid.
		case nil:
			// Do nothing.
		default:
			t.Fatalf("Error parsing HTML: %s", err)
		}
	}
}

func decodeSessionToken(encoded string) []byte {
	decoded, err := base64.RawURLEncoding.DecodeString(encoded)
	if err != nil {
		panic(err)
	}
	return decoded
}

func assertUserIDInSession(t *testing.T, session *scs.SessionManager, token string, expectedID UserID) {
	t.Helper()

	b, found, err := session.Store.Find(token)
	if err != nil {
		t.Fatalf("error finding session in store: %v", err)
	}
	if !found {
		t.Errorf("session not found in store")
	}
	_, values, err := session.Codec.Decode(b)
	if err != nil {
		t.Fatalf("error decoding session data: %v", err)
	}
	gotUserID, ok := values[SessionKeyUserID]
	if !ok {
		t.Fatalf("user ID not associated to session")
	}
	if gotUserID != expectedID {
		t.Errorf("got user ID %d from session, wanted %d", gotUserID, expectedID)
	}
}
