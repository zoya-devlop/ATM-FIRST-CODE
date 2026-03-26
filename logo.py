import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig, ax= plt.subplots()
fig.patch.set_facecolar("black")
ax.set_factcolor("black")
ax.axis("off") 

text = ax.text(0.5 , 0.5 , "zoyhal" ,
               fontsize = 60,
               fontweight = "bold",
               color = "#7f5cff",
               ha="center",
               va="center",
               alpha = 0)

def animate(i):
    text.set_alpha(i/100)
    return text,

ani=animation.FuncAnimation(fig,animate,
                            frames=100,interval=30)

plt.show()