// Action container server for Go runtime (OpenWhisk /init and /run pattern)
package main

import (
	"encoding/json"
	"net/http"
)

type InitRequest struct {
	Code    string `json:"code"`
	Handler string `json:"handler"`
}

type RunRequest map[string]interface{}

func initHandler(w http.ResponseWriter, r *http.Request) {
	var req InitRequest
	json.NewDecoder(r.Body).Decode(&req)

	// Initialize action (stub - Go requires compilation)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

func runHandler(w http.ResponseWriter, r *http.Request) {
	var req RunRequest
	json.NewDecoder(r.Body).Decode(&req)

	// Execute action (stub)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"result": req})
}

func main() {
	http.HandleFunc("/init", initHandler)
	http.HandleFunc("/run", runHandler)
	http.ListenAndServe(":8080", nil)
}
