use std::borrow::Cow;
use std::path::{Component, Path, PathBuf};

/// Normalize a path, removing things like `.` and `..`.
///
/// Source: <https://github.com/rust-lang/cargo/blob/b48c41aedbd69ee3990d62a0e2006edbb506a480/crates/cargo-util/src/paths.rs#L76C1-L109C2>
///
/// CAUTION: Assumes that the path is already absolute.
///
/// CAUTION: This does not resolve symlinks (unlike
/// [`std::fs::canonicalize`]). This may cause incorrect or surprising
/// behavior at times. This should be used carefully. Unfortunately,
/// [`std::fs::canonicalize`] can be hard to use correctly, since it can often
/// fail, or on Windows returns annoying device paths.
///
/// # Errors
///
/// When a relative path is provided with `..` components that extend beyond the base directory.
/// For example, `./a/../../b` cannot be normalized because it escapes the base directory.
#[cfg_attr(not(feature = "non-pep508-extensions"), allow(dead_code))]
pub fn normalize_absolute_path(path: &Path) -> Result<PathBuf, std::io::Error> {
    let mut components = path.components().peekable();
    let mut ret = if let Some(c @ Component::Prefix(..)) = components.peek().copied() {
        components.next();
        PathBuf::from(c.as_os_str())
    } else {
        PathBuf::new()
    };

    for component in components {
        match component {
            Component::Prefix(..) => unreachable!(),
            Component::RootDir => {
                ret.push(component.as_os_str());
            }
            Component::CurDir => {}
            Component::ParentDir => {
                if !ret.pop() {
                    return Err(std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        format!(
                            "cannot normalize a relative path beyond the base directory: {}",
                            path.display()
                        ),
                    ));
                }
            }
            Component::Normal(c) => {
                ret.push(c);
            }
        }
    }
    Ok(ret)
}

/// Normalize the `path` component of a URL for use as a file path.
///
/// For example, on Windows, transforms `C:\Users\ferris\wheel-0.42.0.tar.gz` to
/// `/C:/Users/ferris/wheel-0.42.0.tar.gz`.
///
/// On other platforms, this is a no-op.
#[cfg_attr(not(feature = "non-pep508-extensions"), allow(dead_code))]
pub fn normalize_url_path(path: &str) -> Cow<'_, str> {
    // Apply percent-decoding to the URL.
    let path = urlencoding::decode(path).unwrap_or(Cow::Borrowed(path));

    // Return the path.
    if cfg!(windows) {
        Cow::Owned(
            path.strip_prefix('/')
                .unwrap_or(&path)
                .replace('/', std::path::MAIN_SEPARATOR_STR),
        )
    } else {
        path
    }
}
