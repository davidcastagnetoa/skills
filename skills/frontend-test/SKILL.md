---
name: frontend-test
description: Escribe tests para componentes React, hooks y contextos con Vitest + Testing Library. Usar para anadir cobertura de tests al frontend.
origin: ocralis
---

# Frontend Test Skill

Escribe tests para componentes React, hooks y contextos del frontend Ocralis.

## When to Activate

- Anadir tests a un componente o pantalla existente
- Testear hooks custom o contextos (AuthContext, ThemeContext)
- Validar formularios y flujos de usuario
- Mockear llamadas API
- Mejorar cobertura de tests del frontend

## Setup

### Instalacion

```bash
cd ocralis_frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### vitest.config.ts (extender vite.config.ts)

```typescript
/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
  },
});
```

### Setup File (`src/test/setup.ts`)

```typescript
import "@testing-library/jest-dom";
```

### Script en package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Patrones de Test

### Test de Componente/Pantalla

```typescript
// src/screens/Login/__tests__/Login.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../../../context/AuthContext";
import Login from "../Login";

const renderLogin = () => {
  render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe("Login", () => {
  it("deberia mostrar formulario de login", () => {
    renderLogin();
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
  });

  it("deberia mostrar error con campos vacios", async () => {
    renderLogin();
    const submitBtn = screen.getByRole("button", { name: /iniciar/i });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText(/requerido/i)).toBeInTheDocument();
    });
  });
});
```

### Test de Contexto

```typescript
// src/context/__tests__/AuthContext.test.tsx
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthContext";

describe("AuthContext", () => {
  it("deberia iniciar sin usuario", () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });
    expect(result.current.user).toBeNull();
  });

  it("deberia guardar usuario al hacer login", () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });
    act(() => {
      result.current.login("token", "refresh", {
        id: 1,
        name: "Test",
        email: "t@t.com",
      });
    });
    expect(result.current.user).toBeTruthy();
    expect(result.current.user?.email).toBe("t@t.com");
  });
});
```

### Mock de API

```typescript
import { vi } from "vitest";

vi.mock("../../lib/api", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));
```

### Mock de Servicio

```typescript
import { vi } from "vitest";

vi.mock("../../services/company.service", () => ({
  getCompanies: vi.fn().mockResolvedValue([
    { id: 1, nombre: "Empresa Test", cif: "B12345678" },
  ]),
  createCompany: vi.fn().mockResolvedValue({ id: 2, nombre: "Nueva" }),
}));
```

### Helper: Wrapper con Providers

```typescript
// src/test/helpers.tsx
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";
import { ThemeProvider } from "../context/ThemeContext";

export const AllProviders = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </AuthProvider>
  </BrowserRouter>
);
```

## Estructura de Tests

```
src/
├── test/
│   ├── setup.ts
│   └── helpers.tsx
├── screens/
│   └── Login/__tests__/Login.test.tsx
├── context/
│   └── __tests__/AuthContext.test.tsx
├── components/
│   └── __tests__/ProtectedRoute.test.tsx
└── services/
    └── __tests__/company.service.test.ts
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Framework | Vitest + Testing Library + jsdom |
| Naming | `{Component}.test.tsx` en carpeta `__tests__/` |
| Wrappers | Siempre wrappear con BrowserRouter + AuthProvider |
| Async | Usar `waitFor` para operaciones asincronas |
| User events | Preferir `userEvent` sobre `fireEvent` |
| Descripciones | En espanol |
| Queries | Preferir `getByRole` > `getByText` > `getByTestId` |

## Checklist

- [ ] vitest.config.ts configurado con jsdom
- [ ] Setup file con `@testing-library/jest-dom`
- [ ] Tests de componentes con providers wrapping
- [ ] Tests de contextos con `renderHook`
- [ ] Mocks de API y servicios
- [ ] Tests de formularios (validacion, submit)
- [ ] Tests async con `waitFor`
- [ ] Helper de providers reutilizable
