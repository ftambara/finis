package htmltest

import (
	"bytes"
	"encoding/xml"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/andybalholm/cascadia"
	"golang.org/x/net/html"
)

// GetOne returns the node matching the given query.
//
// Fails if exactly one node is not found.
func GetOne(t *testing.T, n *html.Node, query string) *html.Node {
	t.Helper()

	results := GetAll(t, n, query)
	if len(results) > 1 {
		t.Fatalf("too many results for query %q: %d", query, len(results))
	} else if len(results) == 0 {
		t.Fatalf("no results for query %q", query)
	}
	return results[0]
}

// GetAll returns all nodes matching the given query.
func GetAll(t *testing.T, n *html.Node, query string) []*html.Node {
	t.Helper()

	sel, err := cascadia.Parse(query)
	if err != nil {
		t.Fatalf("error parsing query %q: %v", query, err)
	}
	return cascadia.QueryAll(n, sel)
}

// Attr returns the attribute of node `n` with name `name`.
func Attr(n *html.Node, name string) (value string, found bool) {
	for _, attr := range n.Attr {
		if attr.Key == name {
			return attr.Val, true
		}
	}
	return "", false
}

// ParseHTMLResponse validates the response HTML and parses it as an HTML node.
func ParseHTMLResponse(t *testing.T, res *httptest.ResponseRecorder) *html.Node {
	if res.Code != http.StatusOK {
		t.Errorf("got status %v but wanted %v", res.Code, http.StatusOK)
	}
	if res.Body.Len() == 0 {
		t.Fatal("received empty response body")
	}
	r := bytes.NewReader(res.Body.Bytes())
	AssertHTMLWellFormed(t, r)

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

// AssertAttrEquals asserts that an attribute by name `name` matches value `valWant`.
func AssertAttrEquals(t *testing.T, n *html.Node, name string, valWant string) {
	t.Helper()
	valGot, found := Attr(n, name)
	if !found {
		t.Errorf("attr %s not found", name)
	}
	if valGot != valWant {
		t.Errorf("attr %s value was %s, expected %s", name, valGot, valWant)
	}
}

// AssertAttrPresent asserts that an attribute by name `name` exists and
// is not associated to a value.
func AssertAttrPresent(t *testing.T, n *html.Node, name string) {
	t.Helper()
	AssertAttrEquals(t, n, name, "")
}

// AssertHTMLWellFormed asserts that the given text is valid HTML.
//
// This is not an authoritative check of the validity of the syntax, but
// more of a sanity check.
func AssertHTMLWellFormed(t *testing.T, buffer io.Reader) {
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
