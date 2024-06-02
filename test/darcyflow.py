from fenics import *
import matplotlib.pyplot as plt

# Create mesh and define function space
mesh = UnitSquareMesh(32, 32)
V = FunctionSpace(mesh, 'P', 1)

# Define boundary condition
u_D = Constant(0)

def boundary(x, on_boundary):
    return on_boundary

bc = DirichletBC(V, u_D, boundary)

# Define the variable coefficient a(x), change this as needed
a = Expression('1 + x[0]*x[0] + x[1]*x[1]', degree=2)

# Define the source function f(x)
f = Constant(-6.0)

# Define the variational problem
u = TrialFunction(V)
v = TestFunction(V)
a_variational = a * dot(grad(u), grad(v)) * dx
L = f * v * dx

# Compute solution
u = Function(V)
solve(a_variational == L, u, bc)

# Plot solution and mesh
plot(u)
plt.show()