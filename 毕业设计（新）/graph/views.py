from django.shortcuts import render
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from io import BytesIO
import base64


def graph_view(request):
    equation = request.GET.get('equation', 'x**2')
    x = sp.symbols('x')
    expr = sp.sympify(equation)

    x_vals = np.linspace(-10, 10, 400)
    y_vals = [expr.subs(x, val) for val in x_vals]

    plt.figure()
    plt.plot(x_vals, y_vals, label=f"y = {equation}")
    plt.xlabel('x')
    plt.ylabel('y')
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    plt.close()

    return render(request, 'graph/graph.html', {'image': img_str})
