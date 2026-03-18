package main

import (
	"context"
	"errors"
	"fmt"
	"html/template"
	"io"
	"net/http"
	"net/url"

	"github.com/alexedwards/scs/v2"
	"github.com/gorilla/schema"
)

const SessionKeyUserID = "authenticatedUserID"

var (
	// According to gorilla/schema:
	// > Set a Decoder instance as a package global, because it caches
	// > meta-data about structs, and an instance can be shared safely.
	formDecoder = schema.NewDecoder()
	// Likewise for encoders.
	formEncoder = schema.NewEncoder()
)

type FormEncoder interface {
	EncodeForm() (url.Values, error)
}

// TODO(ftambara): Be more descriptive with the error (include the ID).
var ErrUserNotFound = errors.New("user not found")

type UserStore interface {
	Create(ctx context.Context, Email string, Password string) (*User, error)
	All(ctx context.Context) ([]*User, error)
	FetchByID(ctx context.Context, id UserID) (*User, error)
}

type UserID = int32

type User struct {
	ID       UserID
	Email    string // TODO(ftambara): Discriminate between validated and unvalidated emails.
	Password string // TODO(ftambara): Store password or password hash?
}

type UserCreateForm struct {
	Email                string `schema:"user-email,required"`
	Password             string `schema:"user-password,required"`
	PasswordConfirmation string `schema:"user-password-confirmation,required"`
}

var _ FormEncoder = (*UserCreateForm)(nil)

func (u UserCreateForm) EncodeForm() (url.Values, error) {
	form := url.Values{}
	err := formEncoder.Encode(u, form)
	if err != nil {
		return nil, fmt.Errorf("error encoding UserCreateForm: %w", err)
	}
	return form, nil
}

func RegistrationGet(tmpl *template.Template) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		// TODO(ftambara): Handle handler errors in a nice way.
		err := tmpl.Execute(w, nil)
		if err != nil {
			panic(err)
		}
	}
}

type SessionToken [20]byte

// TODO(ftambara): Show password tips as the user types. E.g.
// 	“minimum length 12 characters” only shown when the condition is not met

// TODO(ftambara): Track guest users with a session-attach middleware

// TODO(ftambara): Protect against XSS.

func AccountsCreate(tmpl *template.Template, store UserStore, session *scs.SessionManager) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		// TODO(ftambara): Validate data. If errors are found, render the form again.
		if false {
			// e.g. check email is unique.
			err := tmpl.Execute(w, nil)
			if err != nil {
				panic(err)
			}
		}
		err := req.ParseForm()
		if err != nil {
			panic(err)
		}
		defer func(Body io.ReadCloser) {
			// TODO(ftambara): Think how to handle these types of errors.
			_ = Body.Close()
		}(req.Body)

		// Create the new user.
		var input UserCreateForm
		err = formDecoder.Decode(&input, req.PostForm)
		if err != nil {
			// TODO(ftambara): Fail indicating form issues.
			panic(err)
		}
		// Move to blog.
		// I cannot expose the creation of a User, if my intention is for the ID to be generated
		// by the storage system. In that case, I need one, or many factory functions that
		// persist the model to the storage system, and returning the domain object.
		// This begs the question: have a user creation function type and multiple implementers vs
		// have a concrete function that takes in a store interface and uses it.
		user, err := store.Create(req.Context(), input.Email, input.Password)
		if err != nil {
			// TODO(ftambara): Fail creation issues or internal server error.
			panic(err)
		}

		err = session.RenewToken(req.Context())
		if err != nil {
			// TODO(ftambara): Handle this error.
			panic(err)
		}
		session.Put(req.Context(), SessionKeyUserID, user.ID)

		w.Header().Set("Location", "/accounts/verify")
		w.WriteHeader(http.StatusSeeOther)
	}
}
