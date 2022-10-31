from setuptools import Extension, setup

root = "cpp/"
src = [
    root + fn
    for fn in [
        "NPWordBeamSearch.cpp",
        "WordBeamSearch.cpp",
        "PrefixTree.cpp",
        "LanguageModel.cpp",
        "Beam.cpp",
    ]
]
inc = ["cpp/pybind/"]

word_beam_search_ext = Extension(
    "word_beam_search",
    sources=src,
    include_dirs=inc,
    language="c++",
    extra_compile_args=["-std=c++11"],
)
setup(
    name="word-beam-search",
    version="1.0.1",
    author="Harald Scheidl",
    install_requires=["numpy"],
    python_requires=">=3.5.0",
    ext_modules=[word_beam_search_ext],
    include_package_data=False,
)
