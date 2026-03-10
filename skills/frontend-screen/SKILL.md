---
name: frontend-screen
description: Completa o crea pantallas React con Shadcn UI, React Hook Form y Zod siguiendo los patrones del proyecto Ocralis. Usar para completar las ~20 pantallas parciales del frontend.
origin: ocralis
---

# Frontend Screen Skill

Completa o crea pantallas React siguiendo los patrones del proyecto Ocralis.

## When to Activate

- Crear una nueva pantalla/pagina en el frontend
- Completar una pantalla parcial existente
- Conectar una pantalla con un servicio API
- Agregar formularios con validacion

## Estructura de una Pantalla

```
src/screens/{ScreenName}/
├── {ScreenName}.tsx    # Componente principal
└── index.ts            # Re-export: export { default } from "./{ScreenName}"
```

## Patron Base — Listado con Fetch

```tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { toast } from "sonner";
import { getModels } from "../../services/{modulo}.service";

const ScreenName = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await getModels();
        setData(result);
      } catch (err: any) {
        setError(err.response?.data?.error || "Error al cargar datos");
        toast.error("Error al cargar datos");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="flex justify-center p-8">Cargando...</div>;

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h1 className="text-2xl font-bold">Titulo</h1>
      {/* Contenido */}
    </div>
  );
};

export default ScreenName;
```

## Patron — Formulario (React Hook Form + Zod)

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const formSchema = z.object({
  nombre: z.string().min(1, "Nombre requerido"),
  email: z.string().email("Email invalido"),
});

type FormData = z.infer<typeof formSchema>;

const CreateScreen = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await createModel(data);
      toast.success("Creado correctamente");
      navigate("/ruta-destino");
    } catch (err: any) {
      toast.error(err.response?.data?.error || "Error al crear");
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Crear recurso</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="text-sm font-medium">Nombre</label>
          <Input {...register("nombre")} placeholder="Nombre" />
          {errors.nombre && <p className="text-red-500 text-sm mt-1">{errors.nombre.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium">Email</label>
          <Input {...register("email")} type="email" placeholder="email@ejemplo.com" />
          {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
        </div>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Guardando..." : "Guardar"}
        </Button>
      </form>
    </div>
  );
};
```

## Patron — Responsive: Cards Movil + Tabla Desktop

```tsx
{/* Vista movil */}
<div className="md:hidden space-y-3">
  {data.map(item => (
    <Card key={item.id}>
      <CardContent className="p-4">
        <p className="font-medium">{item.nombre}</p>
        <p className="text-sm text-muted-foreground">{item.email}</p>
      </CardContent>
    </Card>
  ))}
</div>

{/* Vista desktop */}
<div className="hidden md:block">
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Nombre</TableHead>
        <TableHead>Email</TableHead>
        <TableHead>Acciones</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {data.map(item => (
        <TableRow key={item.id}>
          <TableCell>{item.nombre}</TableCell>
          <TableCell>{item.email}</TableCell>
          <TableCell>
            <Button variant="ghost" size="sm" onClick={() => navigate(`/detalle/${item.id}`)}>
              <Edit className="h-4 w-4" />
            </Button>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
</div>
```

## Registrar Ruta en App.tsx

```tsx
<Route path="/nueva-ruta" element={
  <ProtectedRoute>
    <StructuredDataProvider>
      <ProtectedLayout>
        <NuevaPantalla />
      </ProtectedLayout>
    </StructuredDataProvider>
  </ProtectedRoute>
} />
```

## Convenciones del Proyecto

| Concepto | Convencion |
|----------|-----------|
| UI | Shadcn UI (Button, Input, Card, Dialog, Table, Alert) |
| Iconos | `lucide-react` (ArrowLeft, Plus, Trash2, Edit, Search, etc.) |
| Estilos | Tailwind CSS con dark mode (`dark:bg-gray-800`, `dark:text-gray-100`) |
| Navegacion | `useNavigate()` de react-router-dom |
| Auth | `useAuth()` del AuthContext |
| OCR data | `useOcr()` del StructuredDataContext (si aplica) |
| Notificaciones | `toast.success()` / `toast.error()` de Sonner |
| Responsive | Mobile-first, `md:` breakpoint para desktop |
| Loading | Estado `loading` con skeleton o "Cargando..." |
| Errores | Estado `error` con toast y mensaje visual |

## Checklist

- [ ] Componente creado con estados loading/error
- [ ] Conectado al servicio API correspondiente
- [ ] Formulario con React Hook Form + Zod si aplica
- [ ] Responsive (mobile cards + desktop table)
- [ ] Dark mode compatible (`dark:` classes)
- [ ] Toast para feedback al usuario (success/error)
- [ ] Ruta registrada en App.tsx con ProtectedRoute
- [ ] `index.ts` con re-export
