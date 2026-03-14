package main

import (
	"html/template"
	"net/http"
)

func SignUpGet(tmpl *template.Template) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		tmpl.Execute(w, nil)
	}
}
