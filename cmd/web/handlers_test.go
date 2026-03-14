package main

import (
	"bytes"
	"encoding/xml"
	"html/template"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/andybalholm/cascadia"
	"golang.org/x/net/html"
)

func TestSignUpGet(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/sign-up", http.NoBody)
	res := httptest.NewRecorder()

	tmpl := template.Must(parseTemplate("signup.html.tmpl"))
	SignUpGet(tmpl)(res, req)

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

func TestSignUpTemplate(t *testing.T) {
	buf := renderTemplate("signup.html.tmpl")
	assertHTMLWellFormed(t, buf)
}

func renderTemplate(name string) *bytes.Buffer {
	tmpl := template.Must(parseTemplate(name))
	var buf bytes.Buffer
	// TODO(ftambara): Test non-nil template data rendering
	err := tmpl.Execute(&buf, nil)
	if err != nil {
		panic(err)
	}
	return &buf
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
