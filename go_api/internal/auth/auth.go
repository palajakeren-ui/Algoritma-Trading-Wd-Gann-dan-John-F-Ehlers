// ============================================================================
// JWT AUTHENTICATION — Live Trading Security
// ============================================================================

package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// Configuration
const (
	TokenExpiry    = 24 * time.Hour
	RefreshExpiry = 7 * 24 * time.Hour
	APIKeyLength   = 32
)

// Errors
var (
	ErrInvalidToken    = errors.New("invalid token")
	ErrExpiredToken    = errors.New("token expired")
	ErrInvalidAPIKey   = errors.New("invalid api key")
	ErrUnauthorized    = errors.New("unauthorized")
	ErrForbidden       = errors.New("forbidden")
)

// Permissions
type Permission int

const (
	PermRead Permission = 1 << iota
	PermWrite
	PermTrade
	PermAdmin
	PermSuper = PermRead | PermWrite | PermTrade | PermAdmin
)

// Claims represents JWT claims
type Claims struct {
	UserID      uint64     `json:"user_id"`
	Username    string     `json:"username"`
	Permissions Permission `json:"permissions"`
	jwt.RegisteredClaims
}

// APIKey represents an API key
type APIKey struct {
	ID          uint64
	KeyHash     string
	Name        string
	Permissions Permission
	CreatedAt   time.Time
	LastUsed    time.Time
	Active      bool
}

// AuthManager handles authentication
type AuthManager struct {
	jwtSecret    []byte
	apiKeys      map[string]*APIKey
	apiKeysMu    sync.RWMutex
	tokenExpiry  time.Duration
	refreshExp   time.Duration
}

var (
	authManager *AuthManager
	authOnce    sync.Once
)

// InitAuth initializes authentication manager
func InitAuth(secret string) (*AuthManager, error) {
	var initErr error
	
	authOnce.Do(func() {
		if len(secret) < 32 {
			initErr = errors.New("jwt secret must be at least 32 characters")
			return
		}
		
		authManager = &AuthManager{
			jwtSecret:   []byte(secret),
			apiKeys:     make(map[string]*APIKey),
			tokenExpiry: TokenExpiry,
			refreshExp:  RefreshExpiry,
		}
	})
	
	return authManager, initErr
}

// GetAuthManager returns the global auth manager
func GetAuthManager() *AuthManager {
	return authManager
}

// GenerateToken generates a JWT token
func (a *AuthManager) GenerateToken(userID uint64, username string, permissions Permission) (string, error) {
	claims := &Claims{
		UserID:      userID,
		Username:    username,
		Permissions: permissions,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(a.tokenExpiry)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    "cenayang-market",
		},
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(a.jwtSecret)
}

// GenerateRefreshToken generates a refresh token
func (a *AuthManager) GenerateRefreshToken(userID uint64) (string, error) {
	claims := &jwt.RegisteredClaims{
		Subject:   fmt.Sprintf("%d", userID),
		ExpiresAt: jwt.NewNumericDate(time.Now().Add(a.refreshExp)),
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		Issuer:    "cenayang-market-refresh",
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(a.jwtSecret)
}

// ValidateToken validates a JWT token
func (a *AuthManager) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return a.jwtSecret, nil
	})
	
	if err != nil {
		if errors.Is(err, jwt.ErrTokenExpired) {
			return nil, ErrExpiredToken
		}
		return nil, ErrInvalidToken
	}
	
	claims, ok := token.Claims.(*Claims)
	if !ok {
		return nil, ErrInvalidToken
	}
	
	return claims, nil
}

// GenerateAPIKey generates a new API key
func (a *AuthManager) GenerateAPIKey(name string, permissions Permission) (string, error) {
	// Generate random key
	keyBytes := make([]byte, APIKeyLength)
	if _, err := rand.Read(keyBytes); err != nil {
		return "", err
	}
	
	apiKey := "cm-" + base64.URLEncoding.EncodeToString(keyBytes)
	
	// Hash the key for storage
	hash := sha256.Sum256([]byte(apiKey))
	keyHash := hex.EncodeToString(hash[:])
	
	// Store key info
	a.apiKeysMu.Lock()
	defer a.apiKeysMu.Unlock()
	
	a.apiKeys[keyHash] = &APIKey{
		KeyHash:     keyHash,
		Name:        name,
		Permissions: permissions,
		CreatedAt:   time.Now(),
		Active:      true,
	}
	
	return apiKey, nil
}

// ValidateAPIKey validates an API key
func (a *AuthManager) ValidateAPIKey(apiKey string) (*APIKey, error) {
	// Check prefix
	if !strings.HasPrefix(apiKey, "cm-") {
		return nil, ErrInvalidAPIKey
	}
	
	// Hash the key
	hash := sha256.Sum256([]byte(apiKey))
	keyHash := hex.EncodeToString(hash[:])
	
	a.apiKeysMu.RLock()
	defer a.apiKeysMu.RUnlock()
	
	key, exists := a.apiKeys[keyHash]
	if !exists || !key.Active {
		return nil, ErrInvalidAPIKey
	}
	
	// Update last used
	key.LastUsed = time.Now()
	
	return key, nil
}

// RevokeAPIKey revokes an API key
func (a *AuthManager) RevokeAPIKey(keyHash string) error {
	a.apiKeysMu.Lock()
	defer a.apiKeysMu.Unlock()
	
	if key, exists := a.apiKeys[keyHash]; exists {
		key.Active = false
		return nil
	}
	
	return ErrInvalidAPIKey
}

// ListAPIKeys lists all API keys (without hashes)
func (a *AuthManager) ListAPIKeys() []map[string]interface{} {
	a.apiKeysMu.RLock()
	defer a.apiKeysMu.RUnlock()
	
	keys := make([]map[string]interface{}, 0, len(a.apiKeys))
	for _, key := range a.apiKeys {
		keys = append(keys, map[string]interface{}{
			"key_hash":   key.KeyHash[:8] + "...",
			"name":       key.Name,
			"permissions": key.Permissions,
			"created_at": key.CreatedAt,
			"last_used":  key.LastUsed,
			"active":     key.Active,
		})
	}
	return keys
}

// Middleware

// JWTMiddleware validates JWT tokens
func (a *AuthManager) JWTMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, `{"error":"missing authorization header"}`, http.StatusUnauthorized)
			return
		}
		
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, `{"error":"invalid authorization header"}`, http.StatusUnauthorized)
			return
		}
		
		claims, err := a.ValidateToken(parts[1])
		if err != nil {
			http.Error(w, `{"error":"`+err.Error()+`"}`, http.StatusUnauthorized)
			return
		}
		
		// Add claims to context
		ctx := SetClaims(r.Context(), claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// APIKeyMiddleware validates API keys
func (a *AuthManager) APIKeyMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiKey := r.Header.Get("X-API-Key")
		if apiKey == "" {
			http.Error(w, `{"error":"missing api key"}`, http.StatusUnauthorized)
			return
		}
		
		key, err := a.ValidateAPIKey(apiKey)
		if err != nil {
			http.Error(w, `{"error":"invalid api key"}`, http.StatusUnauthorized)
			return
		}
		
		// Add key to context
		ctx := SetAPIKey(r.Context(), key)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthMiddleware validates either JWT or API Key
func (a *AuthManager) AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try JWT first
		authHeader := r.Header.Get("Authorization")
		if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
			parts := strings.Split(authHeader, " ")
			if len(parts) == 2 {
				claims, err := a.ValidateToken(parts[1])
				if err == nil {
					ctx := SetClaims(r.Context(), claims)
					next.ServeHTTP(w, r.WithContext(ctx))
					return
				}
			}
		}
		
		// Try API Key
		apiKey := r.Header.Get("X-API-Key")
		if apiKey != "" {
			key, err := a.ValidateAPIKey(apiKey)
			if err == nil {
				ctx := SetAPIKey(r.Context(), key)
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}
		}
		
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
	})
}

// PermissionMiddleware checks for specific permissions
func (a *AuthManager) PermissionMiddleware(required Permission) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check JWT claims
			claims := GetClaims(r.Context())
			if claims != nil {
				if claims.Permissions&required != 0 {
					next.ServeHTTP(w, r)
					return
				}
				http.Error(w, `{"error":"forbidden"}`, http.StatusForbidden)
				return
			}
			
			// Check API key
			key := GetAPIKey(r.Context())
			if key != nil {
				if key.Permissions&required != 0 {
					next.ServeHTTP(w, r)
					return
				}
				http.Error(w, `{"error":"forbidden"}`, http.StatusForbidden)
				return
			}
			
			http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		})
	}
}

// Context helpers
type ctxKey int

const (
	claimsKey ctxKey = iota
	apiKeyKey
)

func SetClaims(ctx context.Context, claims *Claims) context.Context {
	return context.WithValue(ctx, claimsKey, claims)
}

func GetClaims(ctx context.Context) *Claims {
	if claims, ok := ctx.Value(claimsKey).(*Claims); ok {
		return claims
	}
	return nil
}

func SetAPIKey(ctx context.Context, key *APIKey) context.Context {
	return context.WithValue(ctx, apiKeyKey, key)
}

func GetAPIKey(ctx context.Context) *APIKey {
	if key, ok := ctx.Value(apiKeyKey).(*APIKey); ok {
		return key
	}
	return nil
}

// Constant-time comparison for API keys
func secureCompare(a, b string) bool {
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}
