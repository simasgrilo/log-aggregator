import os
from pathlib import Path
from flask import Blueprint, render_template

doc_app = Blueprint("docs", __name__, 
                    template_folder=os.path.join(Path(__file__).parent.parent, "swagger-ui", "templates"), 
                    static_folder= os.path.join(Path(__file__).parent.parent, "swagger-ui", "static"))


@doc_app.route("/docs")
def get_docs():
    return render_template("index.html")