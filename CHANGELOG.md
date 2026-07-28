# CHANGELOG

<!-- version list -->

## v5.1.8 (2026-07-28)

### Bug Fixes

- **deps**: Update dependencies to latest compatible versions
  ([`3f02cb3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3f02cb31cdde524116dfa02cbb06d83c9c3732ea))

### Chores

- **deps**: Consolidate open dependabot updates
  ([`f98db99`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f98db99bd00f077be62f570711da5e735657f54a))

- **deps**: Update remaining packages to latest compatible versions
  ([`0254df0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0254df0f9fdc3b630d2a51d5f247107dd42ab93c))

- **release**: Sync __init__.py version
  ([`b9f4207`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b9f4207cd5bdac5204036783320c52cdec9a9ff0))

### Continuous Integration

- **release**: Harden back-merge PR (require elevated token, satisfy strict, auto-merge)
  ([`559bb77`](https://github.com/mindhiveoy/pyopenapi_gen/commit/559bb7738d0cb9f520d58b2d704eb17a2c58d069))


## v5.1.7 (2026-07-07)

### Bug Fixes

- Pass Ruff bulk targets via response files
  ([`cd0f263`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cd0f2634acdb00f052f89fe8ee672988c360c5c7))

- **endpoints**: Raise for default-response error codes instead of masking
  ([`89667e4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89667e40496073bb96843d0383ca48abf54b4dd3))

- **transport**: Do not raise HTTPError on non-2xx responses
  ([`f8422aa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f8422aa76783b33b16750d981f4e22a64ef131f0))

### Chores

- **deps**: Consolidate dependabot package updates
  ([`5f08372`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5f08372d037a60a586fa14236e8b32fe9c493547))

- **deps**: Replace safety with pip-audit to drop vulnerable nltk
  ([`6faec80`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6faec80702218502375da989eef26872a677802d))

- **release**: Sync __init__.py version
  ([`6a03c4b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6a03c4b3fb649f8e54bb5ec8fb6e278f28523620))

### Continuous Integration

- **release**: Back-merge release into develop/staging via PR
  ([`3492c51`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3492c514a673ac2f4d19a6b8978d123af11e3173))

### Testing

- Cover optional security requirements
  ([`c26a786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c26a78651fef042fbd3a35cad2c72eea74504851))

- **transport**: Cover full status-code to exception pipeline at runtime
  ([`d2fd83d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d2fd83dddf2285bb9782e90c1d6440b4ba554f31))


## v5.1.6 (2026-03-08)

### Chores

- **release**: Sync __init__.py version
  ([`0b900c0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0b900c0f4bd9a2302ec329ca75c74fa8fd067078))

### Performance Improvements

- **converter**: Eliminate O(N×calls) get_type_hints traversal with module-level caching
  ([`ebefac9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ebefac9947b7bf440957aab09b70cc0f62e08601))


## v5.1.5 (2026-03-08)

### Bug Fixes

- **converter**: Preserve Annotated discriminator in nested dataclass fields
  ([#308](https://github.com/mindhiveoy/pyopenapi_gen/pull/308),
  [`5114aad`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5114aadcead0d239a929e0464322df9a741069d5))

- **converter**: Preserve Annotated discriminator in nested dataclass fields (#308)
  ([#309](https://github.com/mindhiveoy/pyopenapi_gen/pull/309),
  [`382d647`](https://github.com/mindhiveoy/pyopenapi_gen/commit/382d647fca82601a2767d2aaa17bb5354440500d))

### Chores

- **release**: Sync __init__.py version
  ([`6fb5eea`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6fb5eeab9b700e8ebc8aa1bbe83098d2ebc9a427))


## v5.1.4 (2026-03-07)

### Bug Fixes

- **renderer**: Sanitize schema names in discriminator mapping generation
  ([`2f43161`](https://github.com/mindhiveoy/pyopenapi_gen/commit/2f4316190e8cb46211392ed2264a4293bdc69a0f))

### Chores

- **release**: Sync __init__.py version
  ([`c3799e6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c3799e64fd92d2c46b2c847044b8ec7c8309ed3f))


## v5.1.3 (2026-03-03)

### Bug Fixes

- Resolve literal \n in __init__.py and circular imports in models
  ([`8986197`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89861978f6ca07c7dffd04864a240c35604aff1d))

### Chores

- **release**: Sync __init__.py version
  ([`4ca07ea`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4ca07eabd3e9a869549b3cf69226259fcd5c63c0))


## v5.1.2 (2026-02-24)

### Bug Fixes

- **parser**: Remove over-broad component parameter fallback that caused name collisions
  ([`23a8092`](https://github.com/mindhiveoy/pyopenapi_gen/commit/23a8092c91eb6da0c1428d62a29bbdb4dff40013))

### Chores

- **release**: Sync __init__.py version
  ([`974f548`](https://github.com/mindhiveoy/pyopenapi_gen/commit/974f548a54783e6848a3caffbdd78737e6a0f460))


## v5.1.1 (2026-02-13)

### Bug Fixes

- **emitter**: Prevent empty model files with TypeAlias fallback guard
  ([`0b88c84`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0b88c847b80622cd91c32115148efbb25c102dab))

### Chores

- **release**: Sync __init__.py version
  ([`c54a600`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c54a6007e55f6924bb546d1e3662f35805813e3d))


## v5.1.0 (2026-02-10)

### Chores

- **release**: Sync __init__.py version
  ([`27a8846`](https://github.com/mindhiveoy/pyopenapi_gen/commit/27a8846773bd13f8fa24c570eb1bd2e6165cc458))

### Features

- **naming**: Add --naming-strategy CLI option for method name derivation
  ([`89a90ad`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89a90ade6749de3ba2fac726a7a09438d08feadf))


## v5.0.5 (2026-02-06)

### Bug Fixes

- **converter**: Register key transform hooks for generic container types
  ([`0ef725b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0ef725bc3d1bfab8c5ed8b860acc75ed643be9bb))

### Chores

- **release**: Sync __init__.py version
  ([`53a91d5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/53a91d5a004d6a9cecfb64015d2f4cc7a2067eeb))


## v5.0.4 (2026-02-06)

### Bug Fixes

- **parser**: Prevent shared IRSchema corruption in discriminator enum collector
  ([`e93e035`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e93e0357e6e04cf2238a8ae05047712e0826db69))

### Chores

- **release**: Sync __init__.py version
  ([`9816e70`](https://github.com/mindhiveoy/pyopenapi_gen/commit/9816e70c0846bae195cb4c5a7303a84a1e5978da))


## v5.0.3 (2026-01-28)

### Chores

- **release**: Sync __init__.py version
  ([`86d22a9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/86d22a94d0d13510daf50fd9308c9fbe29c830fb))


## v5.0.2 (2026-01-28)

### Bug Fixes

- **discriminator**: Add mapping fallback for shared enum values
  ([`565525f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/565525fbe0a821a2b39317a386a8fbe2a79b42b1))

- **discriminator**: Resolve enum values via schema references
  ([`481ca25`](https://github.com/mindhiveoy/pyopenapi_gen/commit/481ca25fd0da133e2be4fa9106eaa81e2db1d7fe))

### Chores

- **release**: Sync __init__.py version
  ([`f51f356`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f51f3562dfa34ed8932f5e6a2d4e4210ca06c464))


## v5.0.1 (2026-01-28)

### Chores

- **release**: Sync __init__.py version
  ([`b7d0a41`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b7d0a41379ae4f2af647202c1024c67e35144baa))


## v5.0.0 (2026-01-27)

### Bug Fixes

- **core**: Add circular reference protection to DataclassSerializer
  ([`55578f0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/55578f081ac35c18ff8742f24f536d3940f9831d))

- **core**: Update final_module_stem for discriminator enum properties
  ([`b987fa6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b987fa6acc2812082fbd522d758584ed5e3b1ba4))

### Chores

- **release**: Sync __init__.py version
  ([`d2598d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d2598d45f4d3db438bb074254ec1c8aebeb92e32))

### Features

- **core**: Generate unified enums for discriminated unions
  ([`691bcda`](https://github.com/mindhiveoy/pyopenapi_gen/commit/691bcda3275f0aa019c0d3fb1d343d2386b230da))

### Breaking Changes

- **core**: Discriminated union discriminator properties now generate a single unified enum instead
  of multiple single-value enums.


## v4.0.0 (2026-01-22)

### Bug Fixes

- **types**: Preserve OpenAPI anyOf/oneOf order in Union types
  ([`256da40`](https://github.com/mindhiveoy/pyopenapi_gen/commit/256da40a4de2628e3f920badb0ab2ad5f6c0f925))

### Chores

- **release**: Sync __init__.py version
  ([`1c1afee`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1c1afee4187111b51c30934016c2b3d64ed852c0))

### Breaking Changes

- **types**: Generated Union types now preserve OpenAPI anyOf/oneOf order instead of alphabetical
  sorting. This is semantically equivalent but may affect code that relied on sorted order.


## v3.0.2 (2026-01-22)

### Bug Fixes

- **core**: Simplify DataclassSerializer by delegating to cattrs
  ([`d586300`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d586300b4bcb19e904a7705935746f767952c085))

### Chores

- **release**: Sync __init__.py version
  ([`f6cca64`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f6cca64aef2812b29bb41e3b5a306ca64234bfc1))


## v3.0.1 (2026-01-22)

### Bug Fixes

- **core**: Respect cattrs unstructure hooks in DataclassSerializer
  ([`cfb4ba9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cfb4ba9a30f209428c192ccefa572826a6061c3b))

### Chores

- **release**: Sync __init__.py version
  ([`fdd5dc7`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdd5dc710974b59db47736bea34d9d22b2728176))


## v3.0.0 (2026-01-14)

### Bug Fixes

- **parser**: Resolve schema registration and enum naming issues
  ([`5acf246`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5acf2462860702593964c8a052c65b537ff180d5))

### Chores

- **release**: Sync __init__.py version
  ([`a705bcd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a705bcdb1b8fa9b790da0fa6c3bf599c7fdf96e9))

### Code Style

- Apply black formatting to python_construct_renderer.py
  ([`ab95807`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ab95807bd0dd46946d003ec52bdab9e01e118438))

### Breaking Changes

- **parser**: Schema registration now uses sanitized names consistently


## v2.7.5 (2026-01-13)

### Bug Fixes

- **emitters**: Ensure oneOf/anyOf/allOf variants get generation names
  ([`5dfe6db`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5dfe6db9a949ff54f8a30a481890616dc147833e))

### Chores

- **release**: Sync __init__.py version
  ([`0d73483`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0d734835294cfd20a3247280435ff367b805aa89))


## v2.7.4 (2026-01-13)

### Bug Fixes

- **release**: Prevent semantic-release failures from verbose dependency commits
  ([`e0eaa59`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e0eaa5944fdb99515eed827373a9e6936625a864))


## v2.7.3 (2026-01-13)

### Bug Fixes

- **visitor**: Generate Union type alias for oneOf/anyOf discriminated unions
  ([`1f991f3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1f991f3b5804bf6f63a731214649eff34edd2ed5))

### Chores

- **deps**: Update dependencies in poetry.lock
  ([`7478a46`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7478a4666dc6fe9690d29d017b11cab9b04d0044))

- **release**: Sync __init__.py version
  ([`960ed74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/960ed74f4c1e77e3598edc9cf0c690f19c82a5b9))


## v2.7.2 (2025-12-29)

### Bug Fixes

- Correct spelling of "deserialization" and "sanitized" in comments and docstrings
  ([`f7c533c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f7c533c83248c59c9a002cb4e6ed10c9bcf9bb23))

- Register cattrs hooks for additionalProperties wrapper classes
  ([`850fa04`](https://github.com/mindhiveoy/pyopenapi_gen/commit/850fa04dc30de60f045365ddbf9589738557116b))

### Chores

- Add comprehensive documentation for code review, generation, quality checks, and dependency
  management
  ([`32dcd79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/32dcd79a2bf3bd3def3d5a519b543bf5de203825))

- **release**: Sync __init__.py version
  ([`42fa469`](https://github.com/mindhiveoy/pyopenapi_gen/commit/42fa469f2fc8e5b52b91de47846c2d76964c1349))


## v2.7.1 (2025-12-29)

### Bug Fixes

- Handle boolean enums and typeless array items correctly
  ([`0509db9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0509db97ba1aca5808153c360ba79a4814cb1911))

### Chores

- **release**: Sync __init__.py version
  ([`d8dee0c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d8dee0c87641b017889524cdb9f127cd9beabc0a))


## v2.7.0 (2025-12-27)

### Bug Fixes

- **codegen**: Consistent array item type generation and inline enum extraction
  ([`d9fc953`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9fc953b9b6d77237c9415260ea9891261f1a0d7))

### Chores

- **release**: Sync __init__.py version
  ([`e925222`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e925222bb64b696d2a0fb1f095d90a2ad63bb288))

### Documentation

- Synchronise documentation with implementation
  ([`be1ad98`](https://github.com/mindhiveoy/pyopenapi_gen/commit/be1ad98d16319eadfdc7c1ab1c1126d595fa1a49))

### Features

- **formats**: Add extended OpenAPI format mappings
  ([`4e041e8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4e041e83d56dde485acd5c0ca77423b3dc54c35f))

### Testing

- Fix max_depth expectation in all_of_parser test
  ([`d808e48`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d808e48b76fd779761b65e21c7b4ebd8229180bb))


## v2.6.5 (2025-12-23)

### Bug Fixes

- **cattrs**: Improve union error messages and typed wrapper deserialisation
  ([`443c97c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/443c97c4c6ddd49d1ba83ae2d3ba4d0cb5af3204))

### Chores

- **release**: Sync __init__.py version
  ([`a204cc5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a204cc555d3e7036bda89519649090395f9c62a8))


## v2.6.4 (2025-12-23)

### Bug Fixes

- Deserialise typed additionalProperties values into proper types
  ([`0fb31d7`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0fb31d77607ebef0d1e34274ed365a120ff265ba))

- **deps**: Update dependencies and resolve werkzeug CVE-2025-66221
  ([`4c33868`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c33868d198195f75eac3b68f21aaa5064d5a3a8))

- **deps**: Update werkzeug to 3.1.4 for CVE-2025-66221
  ([`faf39ef`](https://github.com/mindhiveoy/pyopenapi_gen/commit/faf39efc84fb29305e5a18794871256b07b9f402))

- **security**: Add explicit permissions to GitHub workflows
  ([`9d97d49`](https://github.com/mindhiveoy/pyopenapi_gen/commit/9d97d4915e77e8b5e2e23f7ecb62722e116eaa13))

- **security**: Remove dead code with ReDoS vulnerability
  ([`1483ea1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1483ea1702ccccd8d4a5b36c6101a81833d36468))

### Chores

- **release**: Sync __init__.py version
  ([`73b2525`](https://github.com/mindhiveoy/pyopenapi_gen/commit/73b2525a32bc9c2a8fc6f2b40bc82a147eca813c))


## v2.6.3 (2025-12-18)

### Bug Fixes

- **generator**: Convert camelCase params to snake_case in overloaded endpoints
  ([`0e1d68a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0e1d68a886ed897edb539aaa896c152c6bfd6cce))

### Chores

- **release**: Sync __init__.py version
  ([`d97ef9c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d97ef9ccc6d232a002fb2a55d7cca04a2cb4e6b8))


## v2.6.2 (2025-12-18)

### Bug Fixes

- **serializer**: Add base64 encoding for bytes in DataclassSerializer
  ([`4b5ced2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4b5ced27ee7bd08d93764a17a84637c9d7c38d86))

### Chores

- Update .gitignore to include coverage.json and new project coordination files
  ([`16c3ee5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/16c3ee5fa1e61badbe8f403e3c25c44fb201b692))

- **release**: Sync __init__.py version
  ([`10734f0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/10734f0e5ddd044d86f1bcb3c633a20201d1defd))

### Refactoring

- Streamline CLAUDE.md for clarity and organization
  ([`653c41c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/653c41caf639bfd92fa5969ea1116284c0a547ee))


## v2.6.1 (2025-12-15)

### Bug Fixes

- **codegen**: Preserve original API field names and detect collisions
  ([`f412351`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f4123510f4b402c9cee55d0d60d3f8b70be7b96e))

### Chores

- **release**: Sync __init__.py version
  ([`7945ac3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7945ac316218d170fbf2200e9d27cd0769369332))


## v2.6.0 (2025-12-15)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- Release develop with batch dependency updates and security fixes
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Release develop with batch dependency updates and security fixes
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **cattrs**: Handle null values in structure hooks
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **core**: Add datetime and date field handling to cattrs converter
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Add datetime and date field handling to cattrs converter
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **core**: Add datetime and date field handling to cattrs converter
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **core**: Add datetime and date field handling to cattrs converter
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **core**: Add datetime and date field handling to cattrs converter
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **core**: Add datetime and date field handling to cattrs converter
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **core**: Add datetime and date field handling to cattrs converter
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **core**: Add datetime and date field handling to cattrs converter
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **core**: Add datetime and date field handling to cattrs converter
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Sync main (v2.0.3 release) into develop
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- Sync main (v2.0.3 release) into develop
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- Sync main (v2.0.3 release) into develop
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- Sync main (v2.0.3 release) into develop
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- Sync main (v2.0.3 release) into develop
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- Sync main (v2.0.3 release) into develop
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- Sync main (v2.0.3 release) into develop
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- Sync main (v2.0.3 release) into develop
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- Sync version 2.0.1 from main to develop
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Sync version 2.0.1 from main to develop
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- Sync version 2.0.1 from main to develop
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- Sync version 2.0.1 from main to develop
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- Sync version 2.0.1 from main to develop
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- Sync version 2.0.1 from main to develop
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- Sync version 2.0.1 from main to develop
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- Sync version 2.0.1 from main to develop
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- Sync version 2.0.1 from main to develop
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- Update IDE settings and test swagger file
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **deps**: Batch update dependencies ([#186](https://github.com/mindhiveoy/pyopenapi_gen/pull/186),
  [`d692306`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6923068e3cc11eb599fbb5d02758b3a70a144ca))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **merge**: Sync version 2.0.2 from main to develop
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **merge**: Sync version 2.0.2 from main to develop
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **merge**: Sync version 2.0.2 from main to develop
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **merge**: Sync version 2.0.2 from main to develop
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **merge**: Sync version 2.0.2 from main to develop
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **merge**: Sync version 2.0.2 from main to develop
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **merge**: Sync version 2.0.2 from main to develop
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **merge**: Sync version 2.0.2 from main to develop
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **merge**: Sync version 2.0.2 from main to develop
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **release**: Merge develop into main for v2.1.0 release
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Merge develop into main for v2.1.0 release
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Merge develop into main for v2.1.0 release
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Merge develop into main for v2.1.0 release
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **release**: Merge develop into main for v2.1.0 release
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **release**: Merge develop into main for v2.1.0 release
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **release**: Merge develop into main for v2.1.0 release
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **release**: Merge develop into main for v2.1.0 release
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **release**: Merge develop into main for v2.1.0 release
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **release**: Sync __init__.py version
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync __init__.py version
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync __init__.py version
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Sync __init__.py version
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **release**: Sync __init__.py version
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **release**: Sync __init__.py version
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **release**: Sync __init__.py version
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **release**: Sync __init__.py version
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **release**: Sync __init__.py version
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **release**: Sync __init__.py version
  ([`370ef24`](https://github.com/mindhiveoy/pyopenapi_gen/commit/370ef24a43414bae94f8acc5d00bd7b4e3608073))

- **release**: Sync __init__.py version [skip ci]
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync __init__.py version [skip ci]
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync __init__.py version [skip ci]
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Sync __init__.py version [skip ci]
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **release**: Sync __init__.py version [skip ci]
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **release**: Sync __init__.py version [skip ci]
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **release**: Sync __init__.py version [skip ci]
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **release**: Sync __init__.py version [skip ci]
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **release**: Sync __init__.py version [skip ci]
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **release**: Sync __init__.py versio…
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync __init__.py versio…
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync __init__.py vers… ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync __init__.py vers… ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync __init__.p… ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync __init__.p… ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync __init__.p… ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Sync version 2.0.3 from main to develop
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **release**: Sync version 2.0.3 from main to develop
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **release**: Sync version 2.0.3 from main to develop
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **release**: Sync version 2.0.3 from main to develop
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **release**: Sync version 2.0.3 from main to develop
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **release**: Sync version 2.0.3 from main to develop
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **release**: Sync version 2.0.3 from main to develop
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **release**: Sync version 2.0.3 from main to develop
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **release**: Sync version 2.0.3 from main to develop
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **sync**: Merge main into develop to resolve conflicts
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **sync**: Merge main v2.3.0 release into develop
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **sync**: Merge main v2.4.0 into develop
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **sync**: Merge main v2.5.0 release into develop
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **sync**: Merge remote develop changes
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **sync**: Sync develop with main v2.2.0 release
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **sync**: Sync develop with main v2.2.0 release
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **sync**: Sync develop with main v2.2.0 release
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **sync**: Sync develop with main v2.2.0 release
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **sync**: Sync develop with main v2.2.0 release
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **sync**: Sync develop with main v2.2.0 release
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **sync**: Sync develop with main v2.2.0 release
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **sync**: Sync develop with main v2.2.0 release
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **sync**: Sync develop with main v2.2.0 release
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

### Continuous Integration

- Bump actions/cache from 4 to 5 ([#174](https://github.com/mindhiveoy/pyopenapi_gen/pull/174),
  [`735b8c9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/735b8c9ec344bf14881a0d06b5ca4c570fe8aac7))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

### Features

- Improve `cattrs_converter`'s support for future annotations and error reporting, and add enum
  default value handling to `dataclass_generator`.
  ([#159](https://github.com/mindhiveoy/pyopenapi_gen/pull/159),
  [`c6ba271`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c6ba271bdf97183e795a6d447768e43940efe4f8))

- Release develop to main with SSL verification and cattrs improvements
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- Release develop to main with SSL verification and cattrs improvements
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- Release develop to main with SSL verification and cattrs improvements
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **cattrs**: Add Union type structure hook for oneOf/anyOf schemas
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **cattrs**: Add union type structure hook for oneOf/anyOf support
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **cattrs**: Add union type structure hook for oneOf/anyOf support
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **cli**: Add URL support for loading OpenAPI specifications
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Datetime/date handling and pipeline optimization
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **core**: Datetime/date handling and pipeline optimization
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **core**: Datetime/date handling and pipeline optimization
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **core**: Datetime/date handling and pipeline optimization
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **core**: Datetime/date handling and pipeline optimization
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **core**: Datetime/date handling and pipeline optimization
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **core**: Datetime/date handling and pipeline optimization
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **core**: Datetime/date handling and pipeline optimization
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **core**: Datetime/date handling and pipeline optimization
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))

- **transport**: Add verify_ssl parameter and fix cattrs null handling
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **transport**: Add verify_ssl parameter to HttpxTransport
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#190](https://github.com/mindhiveoy/pyopenapi_gen/pull/190),
  [`3996752`](https://github.com/mindhiveoy/pyopenapi_gen/commit/39967528238e1173f483d727cacb960e0ef01aca))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#189](https://github.com/mindhiveoy/pyopenapi_gen/pull/189),
  [`c33c4a1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c33c4a109ad10282537db77791e4a345e923273a))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#184](https://github.com/mindhiveoy/pyopenapi_gen/pull/184),
  [`d6ada2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d6ada2d8ac6792a627ae901086e0dae1902f31ee))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#182](https://github.com/mindhiveoy/pyopenapi_gen/pull/182),
  [`19df388`](https://github.com/mindhiveoy/pyopenapi_gen/commit/19df388d05ad09ca6c10a1ec764bb258003d7db7))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#180](https://github.com/mindhiveoy/pyopenapi_gen/pull/180),
  [`bce6e79`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bce6e79d58862af9c6d2159e668f5a21746241c0))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#164](https://github.com/mindhiveoy/pyopenapi_gen/pull/164),
  [`29791dd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/29791dd4bb11c8c24fdbe7712cdf39b4be5ebe68))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#162](https://github.com/mindhiveoy/pyopenapi_gen/pull/162),
  [`aab0ebd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aab0ebd38454d13a8de1cd17fac5c69bf703011b))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#161](https://github.com/mindhiveoy/pyopenapi_gen/pull/161),
  [`3aafdde`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3aafddef3e64cc5fa080758c154c5e9417d72c40))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#155](https://github.com/mindhiveoy/pyopenapi_gen/pull/155),
  [`d5fa8ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5fa8ece771ebbc9b2aeab4a04e13b6430d697b4))


## v2.5.0 (2025-12-15)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- Release develop with batch dependency updates and security fixes
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Add datetime and date field handling to cattrs converter
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Add datetime and date field handling to cattrs converter
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field mapping for catt…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field mapping for catt…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field mapping for ca…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field mapping for ca…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field mapping…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field mapping…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field mappin…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field mappin…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_case field …
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_case field …
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snake_c…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snake_c…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Implement generic camelCase/snak…
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Implement generic camelCase/snak…
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Sync main (v2.0.3 release) into develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- Sync version 2.0.1 from main to develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Sync version 2.0.1 from main to develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **deps**: Batch update dependencies ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **merge**: Sync version 2.0.2 from main to develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **merge**: Sync version 2.0.2 from main to develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **release**: Sync __init__.py version
  ([`d2c1941`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d2c194149d49dd8ca6bc63dd7f7b36412a2eae9f))

- **release**: Sync __init__.py version [skip ci]
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **release**: Sync __init__.py version [skip ci]
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **release**: Sync version 2.0.3 from main to develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **release**: Sync version 2.0.3 from main to develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **sync**: Merge main into develop to resolve conflicts
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **sync**: Merge main into develop to resolve conflicts
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **sync**: Merge main v2.3.0 release into develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **sync**: Merge main v2.3.0 release into develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **sync**: Merge main v2.4.0 into develop
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **sync**: Merge main v2.4.0 into develop
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **sync**: Merge remote develop changes
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **sync**: Merge remote develop changes
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **sync**: Sync develop with main v2.2.0 release
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **sync**: Sync develop with main v2.2.0 release
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Code Style

- Fix extra blank line in cattrs_converter.py
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Continuous Integration

- Bump actions/cache from 4 to 5 ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Bump actions/cache from 4 to 5 ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Features

- Improve `cattrs_converter`'s support for future annotations and error reporting, and add enum
  default value handling to `dataclass_generator`.
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- Improve `cattrs_converter`'s support for future annotations and error reporting, and add enum
  default value handling to `dataclass_generator`.
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **cattrs**: Add Union type structure hook for oneOf/anyOf schemas
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **cattrs**: Add Union type structure hook for oneOf/anyOf schemas
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **cattrs**: Add union type structure hook for oneOf/anyOf support
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **core**: Datetime/date handling and pipeline optimization
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **core**: Datetime/date handling and pipeline optimization
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

- **transport**: Add verify_ssl parameter and fix cattrs null handling
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **transport**: Add verify_ssl parameter and fix cattrs null handling
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#188](https://github.com/mindhiveoy/pyopenapi_gen/pull/188),
  [`88979c4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/88979c449471cf0d3b8d50e234d601670d48b46c))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#185](https://github.com/mindhiveoy/pyopenapi_gen/pull/185),
  [`6e498fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e498fa986ac24b25d5707a0c87c9b5d11841d02))


## v2.4.0 (2025-11-28)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Add datetime and date field handling to cattrs converter
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Implement generic camelCase/snake_case field mapping…
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Implement generic camelCase/snake_case field mappin…
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Implement generic camelCase/snake_case field …
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Implement generic camelCase/snak…
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- Sync version 2.0.1 from main to develop
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **merge**: Sync version 2.0.2 from main to develop
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **release**: Sync __init__.py version
  ([`7401e91`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7401e915ace09d3b8282a56c5a96a7f433023268))

- **release**: Sync __init__.py version [skip ci]
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **release**: Sync version 2.0.3 from main to develop
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **sync**: Merge main into develop to resolve conflicts
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **sync**: Merge main v2.3.0 release into develop
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **sync**: Sync develop with main v2.2.0 release
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

### Features

- Improve `cattrs_converter`'s support for future annotations and error reporting, and add enum
  default value handling to `dataclass_generator`.
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- Release develop to main with SSL verification and cattrs improvements
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **core**: Datetime/date handling and pipeline optimization
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

- **transport**: Add verify_ssl parameter and fix cattrs null handling
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#165](https://github.com/mindhiveoy/pyopenapi_gen/pull/165),
  [`6e07be2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6e07be219b50c8928638a5e92c2f1b609ddeff5a))


## v2.3.0 (2025-11-24)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **core**: Add datetime and date field handling to cattrs converter
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **core**: Implement generic camelCase/snake_case field mapping…
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- Sync version 2.0.1 from main to develop
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **merge**: Sync version 2.0.2 from main to develop
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **release**: Sync __init__.py version
  ([`b619550`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b61955048937347c7b7e445ac093cdccb9d6afe5))

- **release**: Sync __init__.py version [skip ci]
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **release**: Sync version 2.0.3 from main to develop
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **sync**: Sync develop with main v2.2.0 release
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

### Features

- Improve `cattrs_converter`'s support for future annotations and error reporting, and add enum
  default value handling to `dataclass_generator`.
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

- **core**: Datetime/date handling and pipeline optimization
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#160](https://github.com/mindhiveoy/pyopenapi_gen/pull/160),
  [`7588579`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7588579235b186252e1d194168a6368d67016e87))


## v2.2.0 (2025-11-20)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([`2031708`](https://github.com/mindhiveoy/pyopenapi_gen/commit/203170849ad589b2198de88f220f3a104d24bf0e))

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **ci**: Allow workflow_dispatch to bypass commit message skip checks
  ([#151](https://github.com/mindhiveoy/pyopenapi_gen/pull/151),
  [`9859941`](https://github.com/mindhiveoy/pyopenapi_gen/commit/985994102f5a08cd50eb78f3c9a549a675667b48))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#151](https://github.com/mindhiveoy/pyopenapi_gen/pull/151),
  [`9859941`](https://github.com/mindhiveoy/pyopenapi_gen/commit/985994102f5a08cd50eb78f3c9a549a675667b48))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **ci**: Prevent [skip ci] accumulation from breaking semantic-release auto-trigger
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **core**: Add datetime and date field handling to cattrs converter
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **core**: Add datetime and date field handling to cattrs converter
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **core**: Add datetime and date field handling to cattrs converter
  ([#143](https://github.com/mindhiveoy/pyopenapi_gen/pull/143),
  [`0ed40fb`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0ed40fbde3cc41f560539ce489d2728830412486))

- **core**: Add datetime and date field handling to cattrs converter
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#137](https://github.com/mindhiveoy/pyopenapi_gen/pull/137),
  [`3d675c6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3d675c645df3865abd1122ba730efb71312fa903))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **core**: Implement generic camelCase/snake_case field mapping for cat…
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#148](https://github.com/mindhiveoy/pyopenapi_gen/pull/148),
  [`bedcabe`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bedcabee7114c6db7da231a1942d501d6e027e76))

- **core**: Resolve array item schema false positive cycle detection and optimise response
  deserialisation ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#137](https://github.com/mindhiveoy/pyopenapi_gen/pull/137),
  [`3d675c6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3d675c645df3865abd1122ba730efb71312fa903))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- Sync main (v2.0.3 release) into develop
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- Sync main (v2.0.3 release) into develop
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- Sync main (v2.0.3 release) into develop
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- Sync version 2.0.1 from main to develop
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- Sync version 2.0.1 from main to develop
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- Sync version 2.0.1 from main to develop
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- Sync version 2.0.1 from main to develop
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- Sync version 2.0.1 from main to develop
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- Sync version 2.0.1 from main to develop
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- Sync version 2.0.1 from main to develop
  ([#135](https://github.com/mindhiveoy/pyopenapi_gen/pull/135),
  [`bf952a8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bf952a84f69dd4f599180c781c3a68c94cb123f0))

- Sync version 2.0.1 from main to develop
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([`d86becc`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d86becc42a2ef02234e6e9582fadb1d9b5743d17))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([`5379675`](https://github.com/mindhiveoy/pyopenapi_gen/commit/53796755212075e262bb98ccb6eb3b0a65bbfd4c))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **merge**: Sync develop with main to resolve conflicts
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **merge**: Sync version 2.0.2 from main to develop
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **merge**: Sync version 2.0.2 from main to develop
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **merge**: Sync version 2.0.2 from main to develop
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **merge**: Sync version 2.0.2 from main to develop
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **merge**: Sync version 2.0.2 from main to develop
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **merge**: Sync version 2.0.2 from main to develop
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- **merge**: Sync version 2.0.2 from main to develop
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **release**: Merge develop into main for v2.1.0 release
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **release**: Merge develop into main for v2.1.0 release
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **release**: Sync __init__.py version [skip ci]
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **release**: Sync __init__.py version [skip ci]
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **release**: Sync __init__.py version [skip ci]
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- **release**: Sync __init__.py version [skip ci]
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- **release**: Sync __init__.py version [skip ci]
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **release**: Sync __init__.py version [skip ci]
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- **release**: Sync __init__.py version [skip ci]
  ([#135](https://github.com/mindhiveoy/pyopenapi_gen/pull/135),
  [`bf952a8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bf952a84f69dd4f599180c781c3a68c94cb123f0))

- **release**: Sync __init__.py version [skip ci]
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **release**: Sync __init__.py version [skip ci]
  ([`e03ddd0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e03ddd039aa17a710e39e2a5b3bd92a2d5a31f00))

- **release**: Sync version 2.0.3 from main to develop
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **release**: Sync version 2.0.3 from main to develop
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **release**: Sync version 2.0.3 from main to develop
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- **release**: Sync version 2.0.3 from main to develop
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **sync**: Sync develop with main v2.1.0
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **sync**: Sync develop with main v2.1.0
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#147](https://github.com/mindhiveoy/pyopenapi_gen/pull/147),
  [`71e1295`](https://github.com/mindhiveoy/pyopenapi_gen/commit/71e1295900c2361d1c622ca4fe65e58ee08b3b25))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#145](https://github.com/mindhiveoy/pyopenapi_gen/pull/145),
  [`f055f3f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f055f3fc7953f30f10793a5428b3c6cfc027288c))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#141](https://github.com/mindhiveoy/pyopenapi_gen/pull/141),
  [`97483d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97483d4ee4122897bade0f6cd8dc64bf5039cb71))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#139](https://github.com/mindhiveoy/pyopenapi_gen/pull/139),
  [`7faf179`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7faf179bf9994c32353f42a3b510a64486fb9fdb))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([`cd46d6b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cd46d6b3823737a3fa4e6d9b14e02565bae9bb4f))

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

- **workflow**: Add semantic-release commit naming conventions
  ([#151](https://github.com/mindhiveoy/pyopenapi_gen/pull/151),
  [`9859941`](https://github.com/mindhiveoy/pyopenapi_gen/commit/985994102f5a08cd50eb78f3c9a549a675667b48))

### Features

- **core**: Datetime/date handling and pipeline optimization
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **core**: Datetime/date handling and pipeline optimization
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **core**: Datetime/date handling and pipeline optimization
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#153](https://github.com/mindhiveoy/pyopenapi_gen/pull/153),
  [`af39e47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/af39e478908e66f325c7ee418fe240f00ca8f465))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#150](https://github.com/mindhiveoy/pyopenapi_gen/pull/150),
  [`cad4cc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cad4cc1246bc657ce9df0482cf44645a7d6fc442))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#142](https://github.com/mindhiveoy/pyopenapi_gen/pull/142),
  [`6f5efbf`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6f5efbf03c79338db687a0b4a743c1552272f738))

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#149](https://github.com/mindhiveoy/pyopenapi_gen/pull/149),
  [`7f5b80f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f5b80f3f795b169ccee998825c194220b0ae7f6))


## v2.1.0 (2025-11-20)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **core**: Add datetime and date field handling to cattrs converter
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

### Chores

- Sync main (v2.0.3 release) into develop
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- Sync version 2.0.1 from main to develop
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **merge**: Sync version 2.0.2 from main to develop
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **release**: Sync __init__.py version [skip ci]
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

- **release**: Sync __init__.py version [skip ci]
  ([`cb7832b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cb7832beb7bf81471ee10eeeacba5ad74540bfbd))

- **release**: Sync version 2.0.3 from main to develop
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

### Features

- **core**: Datetime/date handling and pipeline optimization
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))

### Performance Improvements

- **ci**: Remove redundant tests and quality checks from release pipeline
  ([#146](https://github.com/mindhiveoy/pyopenapi_gen/pull/146),
  [`f646324`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f64632407305b5d03964222d013f0145baf7c16e))


## v2.0.3 (2025-11-20)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **core**: Implement generic camelCase/snake_case field mapping for cattrs converter
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **core**: Resolve type checking and security issues in cattrs converter
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

### Chores

- Sync version 2.0.1 from main to develop
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **merge**: Sync version 2.0.2 from main to develop
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **release**: Sync __init__.py version [skip ci]
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))

- **release**: Sync __init__.py version [skip ci]
  ([`5f7a70a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5f7a70aaaf1a77d7257c6c3dd826e2bbcf1b9f98))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#140](https://github.com/mindhiveoy/pyopenapi_gen/pull/140),
  [`63c0f3c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63c0f3c75831ee1c6e376d61f99ac8f45c835cb4))


## v2.0.2 (2025-11-20)

### Bug Fixes

- Ensure auto-approve waits for Poetry lock fix workflow
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

### Chores

- Sync version 2.0.1 from main to develop
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

- **deps**: Update poetry.lock for commitizen 4.10.0
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

- **deps**: Update poetry.lock for python-semantic-release 10.5.2
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

- **release**: Prepare v2.0.2 with dependency updates and automation improvements
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

- **release**: Sync __init__.py version [skip ci]
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))

- **release**: Sync __init__.py version [skip ci]
  ([`b52f18f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b52f18ff99780e59d0d2588e26318fa85d481c78))

### Documentation

- Add automated Poetry lock conflict resolution for Claude pipeline
  ([#136](https://github.com/mindhiveoy/pyopenapi_gen/pull/136),
  [`d9749cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d9749cde987440bed9ebb1a4c19196d093f83111))


## v2.0.1 (2025-11-20)

### Bug Fixes

- Remove automatic response unwrapping for schemas with "data" field
  ([`8abe4a9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8abe4a9c798304505e0fd510a0aead99e0a989ce))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`f3e82f6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f3e82f643979e696959d798e850330749442ad1a))

### Code Style

- Apply Black formatting to test files
  ([`ce6472a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ce6472ac827bae9dd0e4b21e68e0dd0d2fee55c0))


## v2.0.0 (2025-11-19)

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`0c5a5b5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0c5a5b5e5dc77da1687aadf02bd47e2819110162))

### Refactoring

- Migrate from BaseSchema to cattrs for 10x performance improvement
  ([`f5a8cec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f5a8cec7b830a0b4435d0b00373d33a350643384))

### Breaking Changes

- Generated clients no longer inherit from BaseSchema. Clients generated with previous versions will
  continue to work, but newly generated clients use cattrs with Meta class for field mappings.


## v1.0.0 (2025-11-19)

### Bug Fixes

- **codegen**: Use proper deserialisation for array type alias responses
  ([`5be1243`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5be12436822ff702a77b1b3b34fa960131623159))

### Chores

- Regenerate poetry.lock
  ([`ca4c2bc`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ca4c2bcdaa7cc53564103e7bfa5f76fe054974fc))

- **release**: Sync __init__.py version [skip ci]
  ([`8b879c8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8b879c8542e14844aa345d5abfc1f7b36612a610))


## v0.23.1 (2025-11-07)

### Bug Fixes

- **schemas**: Add automatic base64 encoding/decoding for bytes fields
  ([`b611b4c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b611b4cf37a5714b15f6cb4840b5ebfc0bbb0079))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`ceeec05`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ceeec0532c6f565ff677f5ca5a31464fd1557513))


## v0.23.0 (2025-11-07)

### Bug Fixes

- **security**: Implement case-insensitive Content-Type header comparison
  ([`cc3606c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cc3606cded8b3f7de4246bacc1fe832f9b5e0559))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`ae8207a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ae8207a150de33caf161b746e2852d60a49cab32))

### Features

- **types**: Add multi-content-type response support with Union types
  ([`8739d3e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8739d3e86ead2bb70761100938ff1d35d7f60c95))


## v0.22.0 (2025-10-27)

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`962813f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/962813f26956b105f2ff6e470d80195343cfc95a))

### Documentation

- **architecture**: Update docs for Protocol and Mock generation
  ([`8574371`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8574371565138dd4ebd59cc5822a813d152e7e26))

- **guides**: Add comprehensive Protocol and Mock generation guide
  ([`aea11da`](https://github.com/mindhiveoy/pyopenapi_gen/commit/aea11dac6c560100e0fc43befc97b3ef6c2069e6))

- **readme**: Update README with auto-generated mock helpers section
  ([`78225a6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/78225a6b8dc16810c54da3bc9eaf4d1f042e4adf))

### Features

- **emitters**: Add MocksEmitter for generating mocks/ package structure
  ([`824d377`](https://github.com/mindhiveoy/pyopenapi_gen/commit/824d377233d01b0d42af1f803d773785e5f1dc38))

- **endpoints**: Add mock helper class generation with NotImplementedError stubs
  ([`63bbf51`](https://github.com/mindhiveoy/pyopenapi_gen/commit/63bbf51c38d3994aa3233b06237c05f71950a58b))

- **endpoints**: Add Protocol generation for endpoint structural typing
  ([`1bf42d8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1bf42d84b063647aa2460b2b337601b0fb2d7d46))

### Refactoring

- **visit**: Remove unused protocol_helpers module
  ([`2389fc9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/2389fc9301461a754d169bc5c971dc833ee2a305))

### Testing

- **endpoints**: Add comprehensive Protocol and Mock generation tests
  ([`2da2cfb`](https://github.com/mindhiveoy/pyopenapi_gen/commit/2da2cfbd1d3a47d11a0525e8d8972403588c2ac4))

- **generation**: Add comprehensive tests for Protocol and Mock generation
  ([`89dbb20`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89dbb205ac476510db1e894fa06887c1e71f9ec2))


## v0.21.1 (2025-10-24)

### Bug Fixes

- **codegen**: Fix enum parameter serialization in query, header, and path parameters
  ([`be5391f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/be5391ff9fde14a1826aa217c077b06a0f832f8c))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`823dc4e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/823dc4e7083f17df7323aeebd9a400fd9d7aca5d))


## v0.21.0 (2025-10-23)

### Bug Fixes

- **serialization**: Respect BaseSchema field mappings in DataclassSerializer
  ([`ef5d365`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ef5d3656008417bbae17e6370e33e7b0c12cefd6))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`446d496`](https://github.com/mindhiveoy/pyopenapi_gen/commit/446d4963a1e8428da7b6476088104aac599dae8f))

### Breaking Changes

- **serialization**: DataclassSerializer now correctly maps Python snake_case field names to API
  camelCase field names when serializing BaseSchema instances.


## v0.20.1 (2025-10-21)

### Bug Fixes

- **codegen**: Resolve method naming and file handling in overloaded endpoints
  ([`190e581`](https://github.com/mindhiveoy/pyopenapi_gen/commit/190e5819e99edf37d14722b075069851d03c4c3b))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`8047e53`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8047e53df11d8985d95f89dbf3b36046af1e6f1a))


## v0.20.0 (2025-10-19)

### Bug Fixes

- **serializer**: Handle enum instances in DataclassSerializer serialization
  ([`7eaf8ed`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7eaf8ed07e6b975ecd33ec0c3a6e642f2f23e205))

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`53c6163`](https://github.com/mindhiveoy/pyopenapi_gen/commit/53c6163b7c536ee17b6bb3a5fb631ed1900a4520))

### Features

- **tests**: Add comprehensive tests for DataclassSerializer with enum support and nested
  dataclasses
  ([`21de6af`](https://github.com/mindhiveoy/pyopenapi_gen/commit/21de6af2fdd33de6212863cc645ed426c6b1cd72))


## v0.19.0 (2025-10-18)

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`4938f48`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4938f4840650dc56573ca3294d782f74ea89dc65))

### Features

- **codegen**: Integrate DataclassSerializer for request body serialization
  ([`0b5b01f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0b5b01f3e7a5a1d7d57298088bf2543920517855))


## v0.18.0 (2025-10-14)

### Bug Fixes

- **ci**: Add github_token to Claude Code action
  ([`e3a18d5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e3a18d5377c206c9735981c588999decdf361fdf))

- **ci**: Allow dependabot in semantic-release and optimize Claude Code reviews
  ([`717e90c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/717e90c3a8bff13757434fb1375b0b7a30968fd9))

### Chores

- **deps**: Update idna to version 3.11 and adjust python version requirement
  ([`a4adacb`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a4adacbda45ec8e9b67b8734b7867188b38c2fc1))

- **release**: Sync __init__.py version [skip ci]
  ([`1f0e3af`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1f0e3af6937d63394c6c0250e19890278f1a7bd1))

### Documentation

- **readme**: Add comprehensive programmatic API documentation
  ([`d2fca57`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d2fca57f62b0a1c5f718401df3c1b8ac7a7bb02b))

### Features

- **codegen**: Add @overload support for multi-content-type operations
  ([`bf608a7`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bf608a7c47dc4c528f407456478002e3d6779886))

- **codegen**: Integrate @overload generation into endpoint method generator
  ([`d29cd13`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d29cd131ed498c389366712eb873430ec0eb7e37))

- **spec**: Update business_swagger.json with multi-content-type example
  ([`5007e77`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5007e7752440856f7111a7422af09ca6da8a5a5a))


## v0.17.0 (2025-10-13)

### Chores

- **release**: Sync __init__.py version [skip ci]
  ([`287f52a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/287f52aeea6de427fb0c3bd8014e5317a9052369))

### Features

- **ci**: Optimize Claude Code workflow and enable bot releases
  ([`c2efbfa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c2efbfa17f29ab040412935cf758c6c92cb1569a))


## v0.16.1 (2025-10-13)

### Bug Fixes

- **version**: Manually sync __init__.py to 0.16.0 after failed workflow
  ([`7ee9090`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7ee90902add14d93d471418b56514a8bcafd81cb))

- **workflow**: Use follow-up commit instead of amending for version sync
  ([`96f2014`](https://github.com/mindhiveoy/pyopenapi_gen/commit/96f2014bb10ecbfbe3873db32ea6a5f8334542a2))


## v0.16.0 (2025-10-13)

### Bug Fixes

- **api**: Improve type annotation for generate_client return type
  ([`f35d99c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f35d99c1d2233a20fdd1a69ef0a175ab902513c4))

- **api**: Update business_swagger.json descriptions and schemas
  ([`6496144`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6496144200fb8dfb28275f0d111138107775fa29))

- **lint**: Correct import ordering in __init__.py for Ruff compliance
  ([`a159807`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a159807fd1932206dd44c805629683998c88707f))

- **release**: Sync __init__.py version automatically in semantic-release workflow
  ([`7f28674`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7f2867449be1b75b2fc4b7c04073fcad3320e865))

- **security**: Address Bandit security warnings with proper logging and nosec annotations
  ([`f9b0ff3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f9b0ff3e73ebeaaed49fc631429835ee6e99a33c))

- **types**: Add binary format mapping to unified type resolver
  ([`ecba081`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ecba081b37a217277ea61d58b30d1f0a7ac2e04d))

### Features

- **api**: Add developer-friendly programmatic API with generate_client()
  ([`ec8ad0c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ec8ad0c7b166e9cb523a91d97f8639f050d940c3))

### Refactoring

- **init**: Remove unused HTTPMethod enum and IR dataclasses
  ([`7b096ed`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7b096ed321612823976a2e7b7a995d0aaf024312))


## v0.15.0 (2025-10-11)

### Bug Fixes

- **release**: Correct semantic-release configuration and sync version to 0.14.3
  ([`cfa0813`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cfa081393657acfaa0a1c6a29243746748872b28))

- **types**: Correct self-import detection to avoid false positives with similar filenames
  ([`cfee36e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/cfee36e4c8c57d84c0c1d967a7936c5daddf2197))

### Features

- **versioning**: Add version synchronization validation script and integrate into quality checks
  ([`de2ecb8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/de2ecb8c63711230e890bae1cf79f22d5594c551))


## v0.14.3 (2025-10-11)

### Bug Fixes

- **core**: Resolve ImportError for sibling core packages in shared mode
  ([`5f76cac`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5f76caca6f13ef786e8920fb52dca9e1d02f5dbe))

### Chores

- **deps**: Update dependencies in poetry.lock
  ([`fcfa26c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fcfa26c47b4cbce01eb7a4ccd68c02f5bf4d8c02))


## v0.14.2 (2025-10-10)

### Bug Fixes

- **endpoints**: Prevent _2_2 suffix accumulation in multi-tag operations
  ([`89e500f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89e500f9c9963492454bc3177fabf872052baac5))


## v0.14.1 (2025-10-10)

### Bug Fixes

- **exceptions**: Sort alias names before generating __all__ list
  ([`3a623ec`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3a623ecde7457410ab3c0ed2a62adfdb378d3f6a))

- **helpers**: Modernize TypeCleaner for Python 3.9+ type syntax and union preservation
  ([`856fc33`](https://github.com/mindhiveoy/pyopenapi_gen/commit/856fc330752fa1046aac0fb028376329569d8b99))

- **parsing**: Add type annotation for additionalProperties field to resolve mypy error
  ([`6d4244a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6d4244a00a35d375c666510ec61754c1d36774e8))

### Code Style

- **format**: Apply Black formatting to modernised type syntax changes
  ([`3fb6baa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3fb6baaf6d1e2c1918cd0d64935f7d5a390daadc))

- **format**: Apply Ruff auto-formatting to entire codebase
  ([`3b0ab6b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3b0ab6bcabe4caeee33a0e09f83bf28f58bfde76))

- **lint**: Remove unused TypeFinalizer import from alias_generator
  ([`7b27e7c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7b27e7c5306c252bd816661e6815395ec431f2ce))

### Refactoring

- **types**: Enforce modern Python 3.10+ type syntax across unified type system
  ([`f642a67`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f642a679760d84aa7f3c3fdbefd856056b8a02bd))

### Testing

- Update test assertions for modern Python 3.10+ type syntax
  ([`9644bf7`](https://github.com/mindhiveoy/pyopenapi_gen/commit/9644bf72d41769510b3d9a6774521ee5fd75b6c9))

- **regression**: Add comprehensive coverage for three critical bug classes
  ([`0b5a7ba`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0b5a7ba44d7b58007ef5ed0d446547ec34f8199f))


## v0.14.0 (2025-10-06)

### Documentation

- Remove legacy commands from development guide
  ([`396680e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/396680e93f15cabc638af0a1170853cfa3d6e5de))

### Features

- **exceptions**: Implement human-readable exception names and shared core registry
  ([`6983037`](https://github.com/mindhiveoy/pyopenapi_gen/commit/69830375a5a8e93b14c6cf2cf7b289093b57a346))

### Performance Improvements

- **postprocess**: Optimize Ruff execution with bulk operations (25x faster)
  ([`eed3c34`](https://github.com/mindhiveoy/pyopenapi_gen/commit/eed3c346da9ddbb9daa1d745e8bc8f8f46c6e9b6))

### Testing

- Update exception tests for human-readable names
  ([`26e2aef`](https://github.com/mindhiveoy/pyopenapi_gen/commit/26e2aef9df2e713a1d4098608f7c191bcd5992ab))


## v0.13.0 (2025-09-08)

### Bug Fixes

- **parser**: Handle non-standard schema types automatically
  ([`b9a82bd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b9a82bd1fe5b1cde73c48a2c8e3148506fb5d029))

### Code Style

- Apply Black formatting to fix CI
  ([`7a89d96`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7a89d96c7eeddaa80cb624ae394c70f574c419bb))

- Remove unused import to fix CI
  ([`82334e9`](https://github.com/mindhiveoy/pyopenapi_gen/commit/82334e99d1aa196d316f71d7a36085bc5f6c35fb))

### Documentation

- Add comprehensive release automation documentation
  ([`46f6f37`](https://github.com/mindhiveoy/pyopenapi_gen/commit/46f6f37d5b933db620f57627d48d4e785f63f6b9))

### Features

- **errors**: Enhance error reporting for unknown schema types
  ([`0f199e5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0f199e511a0d3c2d3bac0db439411dfceab5e8d4))


## v0.12.1 (2025-09-07)

### Bug Fixes

- **parser**: Register inline enum array parameters in parsed_schemas
  ([`b1629e2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b1629e27cce4773e9bec1bb3ac92eeb858a4fa38))

### Code Style

- Apply Black formatting and fix linting issues
  ([`1252f3b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1252f3bfa37568ba9743f283b6cceb3b52a54a1d))


## v0.12.0 (2025-09-07)

### Bug Fixes

- **parser**: Properly handle inline enums in array parameters
  ([`ea4b258`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ea4b258ade22cd7448047eeda83d86afb74c354e))

- **security**: Replace assert statements with proper error handling
  ([`532cb41`](https://github.com/mindhiveoy/pyopenapi_gen/commit/532cb41b2ca513f5ff5ac64ee9d64eb468c7b0db))

### Chores

- **deps**: Update typer and click dependencies
  ([`da2d03a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/da2d03a233153f25b3d1d95460da79da935ce455))

- **git**: Add test_output directory to gitignore
  ([`1063e77`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1063e77fdce39b5a5bbdf21a8734427a7700e80d))

### Code Style

- Apply Black formatting to test file
  ([`7e7e150`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7e7e150e02dac6ac1391841a795ffe46c76b5fac))

- Fix import order per Ruff requirements
  ([`2f1df97`](https://github.com/mindhiveoy/pyopenapi_gen/commit/2f1df9774042b0e47306bae75f5dba0c138b0779))

### Testing

- Skip integration test with inline enum parameter issue
  ([`1b37271`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1b37271f2daca9a4f7bbea9b6da615dbd7f0c2ff))

- Skip known issue test for inline enum arrays in parameters
  ([`c6a8f70`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c6a8f70d5827a14740c9faecab71553bee42669d))


## v0.11.0 (2025-09-06)

### Bug Fixes

- Remove dynamic attribute to fix mypy type checking
  ([`b52a1ca`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b52a1cac4987a295ca0d404ed2155b1ab2136ec8))

- Resolve enum type checking and test compatibility issues
  ([`c9ab9e2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c9ab9e2272a2f4af822ae311674822f658f4f7d3))

- **parser**: Enhance parameter resolution to prefer component schemas
  ([`743f6d4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/743f6d46d86f7288ddfeabf1c2896f6a698fccda))

- **types**: Improve enum resolution to handle promoted schemas
  ([`e44d358`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e44d358e5a995a0a93ca19aa3f24ff53855a1666))

- **visit**: Add fallback for missing response descriptions
  ([`5c9b853`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5c9b853c7cdab4afa5d49adf1c8e8f186e39b6e8))

### Chores

- Update build configuration for coverage reports
  ([`0e6f0ff`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0e6f0ff95c9dbaba0a5920d608641ce29ab1d870))

- **deps**: Update project dependencies
  ([`e4a1469`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e4a146996d1486194ca9503c0788434ba6df409d))

### Code Style

- Apply Black formatting to all modified files
  ([`f1d383b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f1d383b8d8aac31ab5f3fb6536ef88eebb0c242f))

- Fix Ruff linting issues (unused imports)
  ([`973b82a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/973b82ab1db4e92ac37b1b38740e888e603094b5))

### Features

- **enums**: Add support for top-level enum schema promotion
  ([`92afb7c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/92afb7c1964d85def7c8432f56d831d5bfa50a81))

### Refactoring

- **core**: Improve exception handling with optional response object
  ([`466706f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/466706fb2cf9dbc43f374c5e51548c6c7111efd2))

- **generator**: Improve logging and JSON serialization
  ([`30bf5a4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/30bf5a4ef36df27f3d348f17dbb6fd519b450b88))

- **loader**: Improve spec validation error handling
  ([`d42cb7d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d42cb7da9a8ad5244b8d56285bd7614391b51ef9))

### Testing

- Add comprehensive business domain OpenAPI spec
  ([`1710abe`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1710abe46521e148da8217f8236252fe9e93514a))

- Enhance type resolution test coverage
  ([`9a0a4e5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/9a0a4e5933a2a20f5aab9e08d77a442768f1a053))

- **enums**: Add comprehensive tests for enum promotion feature
  ([`8cd7eb2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8cd7eb2b61cce36fb01f495ad4ee689c6e09d75b))


## v0.10.2 (2025-07-17)

### Bug Fixes

- **docs**: Update CLAUDE.md with recent publishing automation improvements
  ([`a3eb8d2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a3eb8d24e08e90f38bfa83c7024941a14ae3e599))


## v0.10.1 (2025-07-17)

### Bug Fixes

- **ci**: Add comprehensive PyPI token validation and version conflict detection
  ([`8a096d5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8a096d5c6a30be7021578bfd904f5e61ffc23d27))


## v0.10.0 (2025-07-17)

### Features

- **ci**: Implement robust twine-based publishing with automated branch synchronization
  ([`2fe82b1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/2fe82b18b8e830cdbadea99e178c9e3c1aeb7350))


## v0.9.0 (2025-07-17)

### Bug Fixes

- Auto-format code with black
  ([`25362a2`](https://github.com/mindhiveoy/pyopenapi_gen/commit/25362a21ba94277614648e8c6a43ae109bd8857c))

- Clean up .gitignore formatting
  ([`dce7a47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/dce7a47ab987554c6d3ec46543265481b0955dda))

- Convert .bandit configuration from INI to YAML format
  ([`a40df8f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a40df8f9f9c879cea1d82a8a99b21ba947174ed4))

- Resolve all test failures and improve async support
  ([`a10502b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a10502bacc65730bbed0124d8a78eea7516ca30c))

- Resolve CLI test failures and f-string issues in tests
  ([`dea0113`](https://github.com/mindhiveoy/pyopenapi_gen/commit/dea011332975052df7cf57bb96b2a9c9e84f781d))

- Resolve f-string syntax errors across codebase
  ([`4248061`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4248061f2905d868bcd3b3467359f49e6ea34118))

- Standardize field mapping quotes to double quotes in code generation
  ([`a789381`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a789381081fe10df885136c3e096cc6ab527fe79))

- **build**: Use python -m build instead of poetry build for semantic release
  ([#47](https://github.com/mindhiveoy/pyopenapi_gen/pull/47),
  [`8243b69`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8243b699172995519553e33cd5afe7d437164376))

- **ci**: Enable ci.yml for PRs to provide required test status check
  ([`84e1283`](https://github.com/mindhiveoy/pyopenapi_gen/commit/84e1283471111f6ddc6b481b6f6c8c26d2313007))

- **ci**: Ensure Poetry is available in PATH for semantic-release build command
  ([#47](https://github.com/mindhiveoy/pyopenapi_gen/pull/47),
  [`8243b69`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8243b699172995519553e33cd5afe7d437164376))

- **ci**: Ensure Poetry is available in PATH for semantic-release build command
  ([#46](https://github.com/mindhiveoy/pyopenapi_gen/pull/46),
  [`3734aac`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3734aacb74eda746375c7d88c45715a1f18f33a1))

- **ci**: Ensure Poetry is available in PATH for semantic-release build command
  ([`0a68f6e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/0a68f6e4ace7fb998c4ddec14c7cf67713d7ce73))

- **ci**: Resolve semantic-release build failure with separate build step
  ([#49](https://github.com/mindhiveoy/pyopenapi_gen/pull/49),
  [`70f0d7a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/70f0d7a971a82c7c2b54df9419a3635a6012966b))

- **ci**: Restore minimal ci.yml to satisfy required branch protection
  ([`ee28f45`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ee28f4532feb2ef16bb0163ed30669d635fcbfa9))

- **deps**: Add missing pytest plugins for testing infrastructure
  ([`9dd1557`](https://github.com/mindhiveoy/pyopenapi_gen/commit/9dd15578c7570ea9c342752a87ac10cdf38b26b1))

- **deps**: Regenerate poetry.lock to include build module dependency
  ([`b54085b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b54085b05e4b1417e430f710826b6af4f5640bbc))

### Chores

- Regenerate poetry.lock after merge
  ([`ca45694`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ca456943afb7e1e1aa6f8eb447171017fc2a3da5))

- Remove temporary debug files and process artifacts
  ([`6055bd7`](https://github.com/mindhiveoy/pyopenapi_gen/commit/6055bd7dd71a163ce9f08ddb5596b89092c5ffb0))

- Update .gitignore to exclude temporary files
  ([`7d1f7fb`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7d1f7fbf8370b1575a7346a9f67d389ef7a84a82))

- **ci**: Remove redundant workflows to eliminate test duplication
  ([`ee0bbdd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ee0bbdde9e033684cd29e55db1eaa48d2b56dcf7))

### Documentation

- Add module-specific CLAUDE.md documentation files
  ([`e3f9ef6`](https://github.com/mindhiveoy/pyopenapi_gen/commit/e3f9ef6d945519c9c81f18f86debb83ac413c0b0))

- Update development documentation and setup guide
  ([`fd27c1c`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fd27c1c6a73861e341e0f6fac49cf4fb648587f4))

### Features

- Improve build system and development environment setup
  ([`a913745`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a91374524ec54621b83285714ec3841c96c5c03a))

- **ci**: Implement semantic release automation with conventional commits
  ([`c68a81e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c68a81e20895cccb23ab9cdb7f6f9084fdb9742f))

### Breaking Changes

- **ci**: Release process now requires conventional commit format for automatic versioning. Manual
  version bumping is deprecated.


## v0.8.9 (2025-06-12)


## v0.8.8 (2025-06-12)


## v0.8.7 (2025-06-12)

### Documentation

- Add Claude GitHub App configuration documentation
  ([`49964ef`](https://github.com/mindhiveoy/pyopenapi_gen/commit/49964ef7751ac88ef523f9b6954a53452da99b74))

### Features

- Enhance Claude GitHub App configuration for PR approvals
  ([`f5c6b2e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/f5c6b2ecb31b573e8df48de036d5a116b62d93bc))


## v0.8.6 (2025-06-12)

### Bug Fixes

- Correct f-string syntax error in import_collector.py
  ([#33](https://github.com/mindhiveoy/pyopenapi_gen/pull/33),
  [`497f5fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/497f5fa0ccdec88f90d515adc5c3fddaa4ed40e7))

- Correct f-string syntax error in import_collector.py
  ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

- Correct f-string syntax error in import_collector.py (#33)
  ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

- Improve Claude GitHub App configuration for auto-approval
  ([#33](https://github.com/mindhiveoy/pyopenapi_gen/pull/33),
  [`497f5fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/497f5fa0ccdec88f90d515adc5c3fddaa4ed40e7))

- Improve Claude GitHub App configuration for auto-approval
  ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

- Pin typer and click versions for compatibility
  ([`a2a04af`](https://github.com/mindhiveoy/pyopenapi_gen/commit/a2a04afe032ebc1697139f065d85ab84de385289))

- Update poetry.lock file to match loosened dependency constraints
  ([`bcc471d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bcc471dc550c30ce755841e9199eabd0256459c6))

### Chores

- Bump version to 0.8.7 ([#33](https://github.com/mindhiveoy/pyopenapi_gen/pull/33),
  [`497f5fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/497f5fa0ccdec88f90d515adc5c3fddaa4ed40e7))

- Bump version to 0.8.7 ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

- Bump version to 0.8.7
  ([`80bbd3d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/80bbd3db7ff149638db15f6732c2a1c3c72f84be))

- Update poetry.lock after dependency constraints
  ([`b7dd6cd`](https://github.com/mindhiveoy/pyopenapi_gen/commit/b7dd6cd6897ff7d0e3afadfe34dabefe255f3aa5))

### Continuous Integration

- Bump codecov/codecov-action from 4 to 5
  ([`634f7d5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/634f7d5da915abb01d05e29e97153c87be06c600))

### Documentation

- Add Claude GitHub App configuration documentation
  ([#33](https://github.com/mindhiveoy/pyopenapi_gen/pull/33),
  [`497f5fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/497f5fa0ccdec88f90d515adc5c3fddaa4ed40e7))

- Add Claude GitHub App configuration documentation
  ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

### Features

- Enhance Claude GitHub App configuration for PR approvals
  ([#33](https://github.com/mindhiveoy/pyopenapi_gen/pull/33),
  [`497f5fa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/497f5fa0ccdec88f90d515adc5c3fddaa4ed40e7))

- Enhance Claude GitHub App configuration for PR approvals
  ([#34](https://github.com/mindhiveoy/pyopenapi_gen/pull/34),
  [`08eae74`](https://github.com/mindhiveoy/pyopenapi_gen/commit/08eae74541dbb529cab01ba202ada0333fe2b4f7))

- Remove upper bounds from dependency constraints for better compatibility
  ([`265f9b4`](https://github.com/mindhiveoy/pyopenapi_gen/commit/265f9b46adbe39c9164fd52f189cf75e21d5f5c5))


## v0.8.5 (2025-06-12)

### Bug Fixes

- Add checkout step to auto-approve workflow
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Add checkout step to auto-approve workflow
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Add mypy cache corruption resilience to post-processing
  ([`7c9fb58`](https://github.com/mindhiveoy/pyopenapi_gen/commit/7c9fb58f14f3c328d3b85f15d2c6a975bcf3bcee))

- Add staging environment to testpypi workflow and remove PR trigger
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Add staging environment to testpypi workflow and remove PR trigger
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Apply Black formatting to resolve CI formatting differences
  ([`5480eab`](https://github.com/mindhiveoy/pyopenapi_gen/commit/5480eab56c9182399a373f4d4a0ffc8fa09e2894))

- Correct response handler logic for error-only operations
  ([`1101f3e`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1101f3ef24f3b0ce4038849d89dbc7ca34dda151))

- Correct status event syntax in auto-merge workflow
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Correct status event syntax in auto-merge workflow
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Correct YAML syntax in automation workflows
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Correct YAML syntax in automation workflows
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Enable CI workflow for staging branch PRs
  ([`22229ab`](https://github.com/mindhiveoy/pyopenapi_gen/commit/22229ab10fa23edd4dd3f6c13730568306fb5911))

- Enable PR checks for staging and main branches
  ([`10d73ba`](https://github.com/mindhiveoy/pyopenapi_gen/commit/10d73ba0d635974eb6dbbb314d2f0a395740cf6b))

- Move TestPyPI publish from main to staging branch
  ([`d384b4b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d384b4b76a6a2db57ce9b6c82a1f11e73388e978))

- Re-enable CI workflow for staging branch PRs
  ([`109003a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/109003a8322520671c0dfb923227047977fc65f2))

- Re-enable previously skipped cycle detection tests
  ([`ddb3108`](https://github.com/mindhiveoy/pyopenapi_gen/commit/ddb310876906c22a5ce36d68112accf85e89c0af))

- Resolve CI import ordering and formatting issues
  ([`8f0a281`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8f0a2819e3dbf61ad8a6e5249952dd227e413ebc))

- Resolve persistent import ordering issues in test files
  ([`8280a44`](https://github.com/mindhiveoy/pyopenapi_gen/commit/8280a44b4b2d25e2e08d06840ac20718efbe529e))

- Resolve Typer CLI compatibility issue preventing integration tests
  ([`64d28d0`](https://github.com/mindhiveoy/pyopenapi_gen/commit/64d28d087698508cf3b6aa9af0cdc5a1eecefe29))

- Resolve Typer/Click CLI compatibility issues completely
  ([`11530b3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/11530b3ff510a98aa3181cd5392e93a7a08ebba1))

- Resolve workflow validation errors and optimize CI
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Resolve workflow validation errors and optimize CI
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Update endpoint method generator test for ResponseStrategy parameter
  ([`4e0fd9b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4e0fd9b0cd7483f36a66171913dc2c3fbe0f3946))

- Update integration test workflow for simplified CLI structure
  ([`999ca52`](https://github.com/mindhiveoy/pyopenapi_gen/commit/999ca528c4e62a5549d70062a952c55a60e576b3))

- Update poetry.lock after pinning Typer version for CLI compatibility
  ([`c01d285`](https://github.com/mindhiveoy/pyopenapi_gen/commit/c01d2856147d063a6daa384d31097e710b4e558f))

- Update poetry.lock after removing Jinja2 dependency
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Update poetry.lock after removing Jinja2 dependency
  ([`994a12a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/994a12a08832c1faa48f66889f85a5f2f28f915f))

- Update poetry.lock after removing Jinja2 dependency
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Update ResponseStrategy tests for simplified no-unwrapping design
  ([`65c906f`](https://github.com/mindhiveoy/pyopenapi_gen/commit/65c906f453fc906c14b2f0c2343a204e31df49cf))

### Chores

- Bump version to 0.8.4 for automation release
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Bump version to 0.8.4 for automation release
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Bump version to 0.8.4 for documentation overhaul release
  ([`42779ca`](https://github.com/mindhiveoy/pyopenapi_gen/commit/42779caf28ef2040d36bd34887309d0db0463236))

- Bump version to 0.8.4 for documentation overhaul release
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Trigger CI workflow for PR status checks
  ([`bd487cf`](https://github.com/mindhiveoy/pyopenapi_gen/commit/bd487cfd01a767994f9f183357633a945e8d789c))

### Documentation

- Professional documentation overhaul and dependency cleanup
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Professional documentation overhaul and dependency cleanup
  ([`153ca4b`](https://github.com/mindhiveoy/pyopenapi_gen/commit/153ca4ba254e67fb3172bca8655164e62e64a185))

- Professional documentation overhaul and dependency cleanup
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Update branch protection documentation with comprehensive settings
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Update branch protection documentation with comprehensive settings
  ([`45583c8`](https://github.com/mindhiveoy/pyopenapi_gen/commit/45583c85fc829959ea808bae7f20052ff7c0f717))

- Update branch protection documentation with comprehensive settings
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

### Features

- Achieve 88% test coverage exceeding 85% target
  ([`89e41aa`](https://github.com/mindhiveoy/pyopenapi_gen/commit/89e41aa7173d611a60889b5f12af64685eb4ff72))

- Add PR automation with auto-merge and auto-approval
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Add PR automation with auto-merge and auto-approval
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Add PR automation with auto-merge and auto-approval workflows
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Add PR automation with auto-merge and auto-approval workflows
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Complete systematic migration of response handler generator tests to ResponseStrategy pattern
  ([`1c7d4f5`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1c7d4f5ed8d6ff11c37ed96a25bc5d058ad06033))

- Enable Claude auto-review for all PRs targeting develop branch
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Enable Claude auto-review for all PRs targeting develop branch
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Enable Claude GitHub App to fix PR issues independently
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Enable Claude GitHub App to fix PR issues independently
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Implement automatic JSON-to-dataclass conversion with field mapping
  ([`1c42a47`](https://github.com/mindhiveoy/pyopenapi_gen/commit/1c42a4754fe9c07c1be19b82da6e808a62cfeae9))

- Production release v0.8.5 - JSON-to-dataclass conversion with ResponseStrategy migration
  ([`d5e9b4a`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d5e9b4a33f6cd277fca6595c2df479bc1cce5bec))

### Refactoring

- Complete ResponseStrategy migration and remove deprecated function
  ([`3671d49`](https://github.com/mindhiveoy/pyopenapi_gen/commit/3671d49e1123275fedc41c178811abecc33e21c6))

- Remove duplicate FieldMapper class and use existing NameSanitizer
  ([`d42f681`](https://github.com/mindhiveoy/pyopenapi_gen/commit/d42f6818b451dab3edbd55a6eaf78cf9aab76306))

- Remove get_return_type_unified function completely from codebase
  ([`eccde2d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/eccde2de2a5a20dca85b4febd376ab0d7640e741))

- Remove unwrapping logic and fix array type alias handling
  ([`97bedc1`](https://github.com/mindhiveoy/pyopenapi_gen/commit/97bedc14355bbb8c970ec39e19290eb09ecc8ea4))

- Replace auto-merge with Claude GitHub App review system
  ([#13](https://github.com/mindhiveoy/pyopenapi_gen/pull/13),
  [`fdf3786`](https://github.com/mindhiveoy/pyopenapi_gen/commit/fdf37868ddcedab065edf959d6f4ababa534499c))

- Replace auto-merge with Claude GitHub App review system
  ([#12](https://github.com/mindhiveoy/pyopenapi_gen/pull/12),
  [`4c9346d`](https://github.com/mindhiveoy/pyopenapi_gen/commit/4c9346d0c41735d60a4fd27ff01f68b0dbacdb51))

- Systematic update to ResponseStrategy pattern
  ([`465c670`](https://github.com/mindhiveoy/pyopenapi_gen/commit/465c670d4932ad520888b5a558c1ad4eaf47aaed))

- Update response handler generator tests to use ResponseStrategy pattern (7/18 completed)
  ([`eafa2c3`](https://github.com/mindhiveoy/pyopenapi_gen/commit/eafa2c3e83d984232d8f48bb23d1a4caec501b2b))


## v0.8.3 (2025-06-11)

- Initial Release
