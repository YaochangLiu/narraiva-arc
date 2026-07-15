# Third-party license inventory

Narraiva Arc currently has **no runtime dependencies** and redistributes no third-party source or
assets. Development tools declared in the `dev` optional dependency group run outside the shipped
package and remain governed by their own licenses.

Every change that adds a distributed runtime dependency, vendored source, model, prompt corpus, or
asset must record its name, version/source, license, copyright notice, and distribution obligations
here before merge. CI performs a dependency vulnerability audit; license compatibility remains a
review responsibility until an automated inventory is introduced.
